#===----------------------------------------------------------------------===##
#
# Part of the LLVM Project, under the Apache License v2.0 with LLVM Exceptions.
# See https://llvm.org/LICENSE.txt for license information.
# SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
#
#===----------------------------------------------------------------------===##

import copy
import itertools
import errno
import os
import time

import lit.Test        # pylint: disable=import-error
import lit.TestRunner  # pylint: disable=import-error

import stl.test.envlst
import stl.test.Test
import stl.util


class StlTestFormat(object):
    """
    Custom test format handler for use with the test format used by msvc stl.
    """

    def __init__(self, default_cxx, execute_external, executor):
        self.execute_external = execute_external
        self.executor = executor
        self.cxx = default_cxx

    def getTestsInDirectory(self, testSuite, path_in_suite,
                            litConfig, localConfig):
        # TODO Make these not asserts
        assert localConfig.envlst_path is not None
        assert os.path.isfile(localConfig.envlst_path)

        source_path = testSuite.getSourcePath(path_in_suite)
        for filename in os.listdir(source_path):
            # Ignore dot files and excluded tests.
            filepath = os.path.join(source_path, filename)
            if filename.startswith('.') or filepath in localConfig.excludes:
                continue

            if not os.path.isdir(filepath):
                if any([filename.endswith(ext)
                        for ext in localConfig.suffixes]):
                    for env_entry, env_num\
                            in zip(stl.test.envlst.parse_env_lst_file(
                            localConfig.envlst_path), itertools.count()):
                        # TODO: Get rid of this copy the excludes dict is
                        # massive
                        test_config = copy.deepcopy(localConfig)
                        test_path_in_suite = path_in_suite + (filename,)

                        yield stl.test.Test.StlTest(testSuite,
                                                    test_path_in_suite,
                                                    litConfig, test_config,
                                                    env_entry, env_num,
                                                    self.cxx)

    def execute(self, test, lit_config):
        result = None
        while True:
            try:
                result = self._execute(test, lit_config)
                break
            except OSError as oe:
                if oe.errno != errno.ETXTBSY:
                    raise
                time.sleep(0.1)

        return result

    def _execute(self, test, lit_config):
        name = test.path_in_suite[-1]
        name_root, name_ext = os.path.splitext(name)
        is_sh_test = name_root.endswith('.sh')
        is_pass_test = name.endswith('.pass.cpp')
        is_fail_test = name.endswith('.fail.cpp')
        is_objcxx_test = name.endswith('.mm')

        if is_sh_test:
            return (lit.Test.UNSUPPORTED,
                    "Sh tests are currently unsupported")

        if is_objcxx_test:
            return (lit.Test.UNSUPPORTED,
                    "Ojbective-C tests are unsupported")

        if test.config.unsupported:
            return (lit.Test.UNSUPPORTED,
                    "A lit.local.cfg marked this unsupported")

        if lit_config.noExecute:
            return lit.Test.Result(lit.Test.PASS)

        script = lit.TestRunner.parseIntegratedTestScript(
                test, require_script=False)

        if isinstance(script, lit.Test.Result):
            return script
        if lit_config.noExecute:
            return lit.Test.Result(lit.Test.PASS)

        tmpDir, tmpBase = lit.TestRunner.getTempPaths(test)

        if is_fail_test:
            return self._evaluate_fail_test(test, test.cxx)
        elif is_pass_test:
            return self._evaluate_pass_test(test, tmpBase, lit_config,
                                            test.cxx)
        else:
            # No other test type is supported
            assert False

    def _clean(self, exec_path):  # pylint: disable=no-self-use
        stl.util.cleanFile(exec_path)
        pass

    def _evaluate_pass_test(self, test, tmpBase, lit_config,
                            test_cxx):
        execDir = os.path.dirname(test.getExecPath())
        source_path = test.getSourcePath()
        exec_path = tmpBase + '.exe'

        should_fail = test.isExpectedToFail()
        pass_var = lit.Test.XPASS if should_fail else lit.Test.PASS
        fail_var = lit.Test.XFAIL if should_fail else lit.Test.FAIL

        # Create the output directory if it does not already exist.
        stl.util.mkdir_p(os.path.dirname(tmpBase))

        try:
            # TODO: Investigate whether or not we want to support compiling
            # and linking in two steps like libcxx. Should be easy.
            cmd, out, err, rc = test_cxx.compileLink(
                source_path, exec_path=exec_path, cwd=execDir)
            compile_cmd = cmd
            if rc != 0:
                report = stl.util.makeReport(cmd, out, err, rc)

                if not should_fail:
                    report += "Compilation failed unexpectedly!"
                lit_config.note(report)
                return lit.Test.Result(fail_var, report)

            # Run the test
            local_cwd = os.path.dirname(source_path)

            cmd, out, err, rc = self.executor.run(exec_path, [exec_path],
                                                  local_cwd, [],
                                                  test.config.environment)
            report = "Compiled With: '%s'\n" % ' '.join(compile_cmd)
            report += stl.util.makeReport(cmd, out, err, rc)

            if rc == 0:
                return lit.Test.Result(pass_var, report)
            else:
                if not should_fail:
                    report += "Compiled test failed unexpectedly!"
                return lit.Test.Result(fail_var, report)

        finally:
            # Note that cleanup of exec_file happens in `_clean()`. If you
            # override this, cleanup is your reponsibility.
            self._clean(exec_path)

    def _evaluate_fail_test(self, test, test_cxx):
        source_path = test.getSourcePath()

        cmd, out, err, rc = test_cxx.compile(source_path, out=os.devnull)
        report = stl.util.makeReport(cmd, out, err, rc)
        if rc != 0:
            return lit.Test.Result(lit.Test.PASS, report)
        else:
            report += 'Expected compilation to fail!\n'
            return lit.Test.Result(lit.Test.FAIL, report)
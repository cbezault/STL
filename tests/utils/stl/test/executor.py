from pathlib import Path
import os


class StepWriter:
    def get_working_directory(step):
        work_dir = Path()
        if str(step.work_dir) == '.':
            work_dir = Path(os.getcwd())
        else:
            work_dir = step.work_dir

        return work_dir

    def merge_environments(current_env, updated_env, appended_vars={'PATH'}):
        result_env = dict(current_env)
        for k, v in updated_env.items():
            if k in appended_vars:
                current_v = result_env.get(k)
                if current_v:
                    result_env[k] = v + ';' + current_v
                else:
                    result_env[k] = v
            else:
                result_env[k] = v
        return result_env

    def write_step_file(self, step, step_file, test_file_handle):
        env = {}
        if step.env:
            env = StepWriter.merge_environments(os.environ, step.env)

        out_cmd = ''
        if env is not None:
            for k, v in env.items():
                out_cmd += 'set ' + k + '=' + v + '\n'

        out_cmd += ('\"%s\"\n' % '\" \"'.join(step.cmd))

        with step_file.open('w') as f:
            print(out_cmd, file=f)

        global_prop_string = \
            'set_property(GLOBAL APPEND PROPERTY STL_LIT_GENERATED_FILES {cmd})'
        print(global_prop_string.format(cmd=step_file.as_posix()),
              file=test_file_handle)


class BuildStepWriter(StepWriter):
    def write(self, test, step, test_file_handle):
        build_base_name = test.getOutputBaseName() + '.build.{}.cmd'
        step_file = \
            test.getOutputDir() / build_base_name.format(str(step.num))
        self.write_step_file(step, step_file, test_file_handle)

        work_dir = StepWriter.get_working_directory(step)

        pass_string = \
            'add_custom_command(OUTPUT {out} COMMAND cmd ARGS /c {cmd} DEPENDS msvcpd_implib msvcp_implib libcpmt libcpmt1 libcpmtd libcpmtd1 libcpmtd0 {cmd} {deps} WORKING_DIRECTORY {cwd})\nadd_custom_target({name} ALL DEPENDS {out})'
        fail_string = \
            'add_test(NAME {name} COMMAND cmd /c {cmd} WORKING_DIRECTORY {cwd})\nset_property(TEST {name} PROPERTY WILL_FAIL TRUE)'

        if not step.should_fail:
            name = test.getFullName() + '_' + str(step.num)
            print(pass_string.format(out=' '.join(map(lambda dep: dep.as_posix(), step.out_files)),
                                     cmd=step_file.as_posix(),
                                     deps=' '.join(map(lambda dep: dep.as_posix(), step.dependencies)),
                                     cwd=work_dir.as_posix(),
                                     name=name),
                  file=test_file_handle)
        else:
            print(fail_string.format(test.getFullName(),
                                     cmd=step_file.as_posix(),
                                     cwd=work_dir.as_posix()),
                  file=test_file_handle)


class LocalTestStepWriter(StepWriter):
    def write(self, test, step, test_file_handle):
        test_base_name = test.getOutputBaseName() + '.test.{}.cmd'
        step_file = \
            test.getOutputDir() / test_base_name.format(str(step.num))
        self.write_step_file(step, step_file, test_file_handle)

        work_dir = StepWriter.get_working_directory(step)

        test_string = \
            'add_test(NAME {name} COMMAND cmd /c {cmd} WORKING_DIRECTORY {cwd})'
        fail_string = \
            'set_property(TEST {name} PROPERTY WILL_FAIL TRUE)'
        depends_string = \
            'set_property(TEST {name} PROPERTY DEPENDS {prev_test})'

        test_name = '"' + test.getFullName() + '_' + str(step.num) + '"'
        print(test_string.format(name=test_name,
                                 cmd=step_file.as_posix(),
                                 cwd=work_dir.as_posix()),
              file=test_file_handle)

        if step.should_fail:
            print(fail_string.format(name=test_name),
                  file=test_file_handle)

        if step.num != 0:
            prev_test = \
                '"' + test.getFullName() + '_' + str(step.num - 1) + '"'
            print(depends_string.format(name=test_name,
                                        prev_test=prev_test),
                  file=test_file_handle)

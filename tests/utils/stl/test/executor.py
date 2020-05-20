from pathlib import Path
import os


def get_working_directory(step):
    work_dir = Path()
    if str(step.work_dir) == '.':
        work_dir = Path(os.getcwd())
    else:
        work_dir = step.work_dir

    return work_dir


class BuildStepWriter:
    def write(self, test, step, test_file_handle):
        work_dir = get_working_directory(step)

        build_cmd = '"' + step.cmd[0] + '"'
        args = '"' + '" "'.join(step.cmd[1:]) + '"'
        build_cmd = build_cmd.replace('\\', '/')
        args = args.replace('\\', '/')

        pass_string = \
            'add_custom_command(OUTPUT {out} COMMAND {cmd} ARGS {args} DEPENDS msvcpd_implib msvcp_implib libcpmt libcpmt1 libcpmtd libcpmtd1 libcpmtd0 {deps} WORKING_DIRECTORY "{cwd}")\nadd_custom_target({test_target} DEPENDS {out})\nadd_dependencies({parent_target} {test_target})'
        fail_string = \
            'add_test(NAME {test_target} COMMAND {cmd} WORKING_DIRECTORY "{cwd}")\nset_property(TEST {test_target} PROPERTY WILL_FAIL TRUE)'
        env_prop = \
            'set_property(TEST {test_target} PROPERTY ENVIRONMENT {env})'

        parent_target = test.mangled_name
        test_target = test.mangled_name + '_' + str(step.num)

        if not step.should_fail:
            out = ' '.join(map(lambda dep: dep.as_posix(), step.out_files))
            deps = \
                '"' + \
                '" "'.join(map(lambda d: d.as_posix(), step.dependencies)) + \
                '"'
            print(pass_string.format(out=out, cmd=build_cmd, args=args,
                                     deps=deps, cwd=work_dir.as_posix(),
                                     test_target=test_target,
                                     parent_target=parent_target),
                  file=test_file_handle)
        else:
            print(fail_string.format(test_target=test.mangled_name,
                                     cmd=build_cmd + ' ' + args,
                                     cwd=work_dir.as_posix()),
                  file=test_file_handle)

            if len(step.env):
                env_list = []
                for k, v in step.env.items():
                    env_list.append(k + '=' + v)
                cmake_env_list = \
                    '"' + \
                    '" "'.join(env_list).replace('\\', '/').replace(';', '\\;') + \
                    '"'

                print(env_prop.format(test_target=test.mangled_name,
                                      env=cmake_env_list),
                      file=test_file_handle)


class LocalTestStepWriter:
    def write(self, test, step, test_file_handle):
        work_dir = get_working_directory(step)

        cmd = '"' + '" "'.join(step.cmd).replace('\\', '/') + '"'

        test_string = \
            'add_test(NAME {name} COMMAND {cmd} WORKING_DIRECTORY "{cwd}")'
        env_prop = \
            'set_property(TEST {name} PROPERTY ENVIRONMENT {env})'
        fail_string = \
            'set_property(TEST {name} PROPERTY WILL_FAIL TRUE)'
        depends_string = \
            'set_property(TEST {name} PROPERTY DEPENDS {prev_test})'

        test_name = test.mangled_name + '_' + str(step.num)
        print(test_string.format(name=test_name,
                                 cmd=cmd,
                                 cwd=work_dir.as_posix()),
              file=test_file_handle)

        if len(step.env):
            env_list = []
            for k, v in step.env.items():
                env_list.append(k + '=' + v)
            cmake_env_list = \
                '"' + \
                '" "'.join(env_list).replace('\\', '/').replace(';', '\\;') + \
                '"'

            print(env_prop.format(name=test_name, env=cmake_env_list),
                  file=test_file_handle)

        if step.should_fail:
            print(fail_string.format(name=test_name),
                  file=test_file_handle)

        if step.num != 0:
            prev_test = \
                test.mangled_name + '_' + str(step.num - 1)
            print(depends_string.format(name=test_name,
                                        prev_test=prev_test),
                  file=test_file_handle)

from pype.utils.queues import yaml_dump


def submit(command, snippet_name, requirements, dependencies, log, profile):
    run_id = yaml_dump(command, snippet_name, requirements,
                       dependencies, log, profile)
    return(run_id)


def post_run(log):
    print(log.__path__)

import click

from .archive.parse import features_from_result, load_archive

from .archive.types import ResultDescription

from .latest import latest_for_app_name


@click.group
@click.option("--app", default=None)
@click.option("--app_version", default=None)
@click.pass_context
def main(ctx: click.Context, app: str, app_version: str | None):
    ctx.ensure_object(dict)
    if app is None:
        print("app is required")
        exit(1)

    case_version, latest_app_version = latest_for_app_name(app)
    app_version = latest_app_version if app_version is None else app_version
    if not case_version or not app_version:
        print("Failed to find test data")
        exit(1)

    ctx.obj["result_description"] = ResultDescription(case_version, app, app_version)


@main.command
@click.pass_context
def list_features(ctx: click.Context):
    result = load_archive(ctx.obj["result_description"])
    features = features_from_result(result)

    for x in features:
        print(x)


@main.command
@click.pass_context
def list_results(ctx: click.Context):
    result = load_archive(ctx.obj["result_description"])

    for x in result.results:
        title_path = x.get("titlePath")
        print(title_path)


if __name__ == "__main__":
    main()

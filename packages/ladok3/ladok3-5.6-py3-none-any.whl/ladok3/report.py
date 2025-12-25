import csv
import datetime
import ladok3
import sys


def report_one_result(ladok, args):
    """Report a single result specified via command line arguments.

    Args:
        ladok (LadokSession): The LADOK session for data access.
        args: Command line arguments containing course, student, component, and grade info.
    """
    if not (
        args.course_code and args.component_code and args.student_id and args.grade
    ):
        print(
            f"{sys.argv[0]} report: "
            "not all positional args given: "
            "course_code, component, student, grade",
            file=sys.stderr,
        )
        sys.exit(1)
    try:
        set_grade(
            ladok,
            args,
            args.student_id,
            args.course_code,
            args.component_code,
            args.grade,
            args.date,
            args.graders,
        )
    except Exception as err:
        student_id = args.student_id
        try:
            student = ladok.get_student(student_id)
        except Exception:
            student = student_id
        print(
            f"{args.course_code} {args.component_code}={args.grade} ({args.date}) "
            f"{student}: {err}",
            file=sys.stderr,
        )


def report_many_results(ladok, args):
    """Report multiple results read from CSV data on stdin.

    Args:
        ladok (LadokSession): The LADOK session for data access.
        args: Command line arguments containing CSV processing options.
    """
    data_reader = csv.reader(sys.stdin, delimiter=args.delimiter)
    for course_code, component_code, student_id, grade, date, *graders in data_reader:
        try:
            set_grade(
                ladok,
                args,
                student_id,
                course_code,
                component_code,
                grade,
                date,
                graders,
            )
        except Exception as err:
            try:
                student = ladok.get_student(student_id)
            except Exception:
                student = student_id
            print(
                f"{course_code} {component_code}={grade} ({date}) {student}: " f"{err}",
                file=sys.stderr,
            )


def set_grade(
    ladok, args, student_id, course_code, component_code, grade, date, graders
):
    """Set a grade for a student's course component result.

    Handles the logic for setting grades, including checking if results are
    already attested, validating dates, and optionally finalizing results.

    Args:
        ladok (LadokSession): The LADOK session for data access.
        args: Command line arguments with options like verbose and finalize.
        student_id (str): Student identifier (personnummer or LADOK ID).
        course_code (str): Course code (e.g., "DD1315").
        component_code (str): Component code (e.g., "LAB1").
        grade (str): Grade to assign (e.g., "P", "F", "A").
        date (str): Examination date in YYYY-MM-DD format.
        graders (list): List of grader identifiers.

    Raises:
        Exception: If the grade setting fails or validation errors occur.
    """
    student = ladok.get_student(student_id)
    try:
        course = student.courses(code=course_code)[0]
    except IndexError:
        raise ladok3.LadokNotFoundError(f"{course_code}: No such course for {student}")
    try:
        component = course.results(component=component_code)[0]
    except IndexError:
        raise ladok3.LadokNotFoundError(
            f"{component_code}: no such component for {course_code}"
        )

    if not component.attested and component.grade != grade:
        if not isinstance(date, datetime.date):
            date = datetime.date.fromisoformat(date)

        if date < course.start:
            print(
                f"{course_code} {component_code}={grade} "
                f"({date}) {student}: "
                f"Grade date ({date}) is before "
                f"course start date ({course.start}), "
                f"using course start date instead."
            )
            date = course.start
        component.set_grade(grade, date)
        if args.finalize:
            component.finalize(graders)
        if args.verbose:
            print(
                f"{course_code} {student}: reported "
                f"{component.component} = {component.grade} ({date}) "
                f"by {', '.join(graders)}."
            )
    elif component.grade != grade:
        raise ladok3.LadokValidationError(
            f"attested {component.component} "
            f"result {component.grade} ({component.date}) "
            f"is different from {grade} ({date})."
        )


def add_command_options(parser):
    """Add the 'report' subcommand options to the argument parser.

    Creates a subparser for result reporting with options for single results
    via command line arguments or batch processing via CSV input.

    Args:
        parser (ArgumentParser): The parent parser to add the subcommand to.
    """
    report_parser = parser.add_parser(
        "report",
        help="Reports course results to LADOK",
        description="Reports course results to LADOK",
    )
    report_parser.set_defaults(func=command)
    one_parser = report_parser.add_argument_group(
        "one result as positional args, only date is optional"
    )
    one_parser.add_argument(
        "course_code",
        nargs="?",
        help="The course code (e.g. DD1315) for which the grade is for.",
    )

    one_parser.add_argument(
        "component_code",
        nargs="?",
        help="The component code (e.g. LAB1) for which the grade is for. "
        "This can be set to the course code (e.g. DD1315) to set the "
        "final grade for the course. But all components must be "
        "certified (attested) before the course grade can be set.",
    )

    one_parser.add_argument(
        "student_id", nargs="?", help="Student identifier (personnummer or LADOK ID)."
    )

    one_parser.add_argument("grade", nargs="?", help="The grade (e.g. A or P).")
    one_parser.add_argument(
        "date",
        nargs="?",
        help="Date on ISO format (e.g. 2021-03-18), "
        f"defaults to today's date ({datetime.date.today()}).",
        type=datetime.date.fromisoformat,
        default=datetime.date.today(),
    )
    one_parser.add_argument(
        "graders",
        nargs="*",
        help="Space separated list of who did the grading, "
        "give each grader as 'First Last <email@institution.se>'.",
    )
    many_parser = report_parser.add_argument_group(
        "many results read from standard input as CSV, columns: "
        "course, component, student, grade, date, grader 1, ..., grader N"
    )
    many_parser.add_argument(
        "-d",
        "--delimiter",
        default="\t",
        help="The delimiter for the CSV input; "
        "default is a tab character to be compatible with POSIX commands, "
        "use `-d,` or `-d ,` to get comma-separated values.",
    )
    many_parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increases the verbosity of the output: -v will print results that "
        "were reported to standard out. Otherwise only errors are printed.",
    )
    report_parser.add_argument(
        "-f",
        "--finalize",
        help="""Finalize the grade (mark as ready/klarmarkera) for examiner to attest.
            Note that without this option, no graders will be registered in LADOK.""",
        action="store_true",
        default=False,
    )


def command(ladok, args):
    """Execute the result reporting command.

    Args:
        ladok (LadokSession): The LADOK session for data access.
        args: Parsed command line arguments containing result data or CSV options.
    """
    if args.course_code:
        report_one_result(ladok, args)
    else:
        report_many_results(ladok, args)

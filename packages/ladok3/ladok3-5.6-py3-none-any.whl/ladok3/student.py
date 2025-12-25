import csv
import ladok3.cli


def print_student_data(student, args):
    """Prints the student data, all attributes, to stdout.

    Args:
      student: A Student object with the student's data
      args: Command line arguments, including flags like --contact
    """
    print(f"First name:   {student.first_name}")
    print(f"Last name:    {student.last_name}")
    print(f"Personnummer: {student.personnummer}")
    print(f"LADOK ID:     {student.ladok_id}")
    print(f"Alive:        {student.alive}")
    print(f"Suspended:    ", end="")
    if any(map(lambda x: x.is_current, student.suspensions)):
        print("YES")
    else:
        print("no")
    if student.suspensions:
        print(f"Suspenions:   ", end="")
        for suspension in student.suspensions:
            print(f"{suspension}", end="\n              ")
        print()
    if args.contact:
        print("Contact information:")
        if student.email:
            print(f"Email:        {student.email}")
        if student.phone:
            print(f"Phone:        {student.phone}")
        if student.address:
            print(f"Address:      {student.address[0]}")
            for line in student.address[1:]:
                print(f"              {line}")


def print_course_data(student, args):
    """Prints the courses"""
    print("Courses:")
    for course in student.courses(code=args.course):
        print(f"{course}")
        if args.results:
            for result in course.results():
                print(f"  {result}")


def add_command_options(parser):
    """Add the 'student' subcommand options to the argument parser.

    Creates a subparser for displaying student information with options
    for course filtering and result display.

    Args:
        parser (ArgumentParser): The parent parser to add the subcommand to.
    """
    student_parser = parser.add_parser(
        "student",
        help="Shows a student's information in LADOK",
        description="""
    Show a student's information in LADOK.
    Shows information like name, personnummer, contact information.
    """,
    )
    student_parser.set_defaults(func=command)
    student_parser.add_argument(
        "id", help="The student's ID, either personnummer or LADOK ID"
    )
    student_parser.add_argument(
        "-c",
        "--course",
        nargs="?",
        const=".*",
        help="A regular expression for which course codes to list, "
        "use no value for listing all courses.",
    )
    student_parser.add_argument(
        "-r",
        "--results",
        action="store_true",
        default=False,
        help="Set to include results for each course listed.",
    )
    student_parser.add_argument(
        "--contact",
        action="store_true",
        default=False,
        help="Include contact information (email, phone, address).",
    )


def command(ladok, args):
    """Execute the student information display command.

    Args:
        ladok (LadokSession): The LADOK session for data access.
        args: Parsed command line arguments containing student ID and display options.
    """
    try:
        student = ladok.get_student(args.id)
        student.alive
    except Exception as err:
        ladok3.cli.err(-1, f"can't fetch student data for {args.id}: {err}")

    print_student_data(student, args)

    if args.course:
        print()
        print_course_data(student, args)

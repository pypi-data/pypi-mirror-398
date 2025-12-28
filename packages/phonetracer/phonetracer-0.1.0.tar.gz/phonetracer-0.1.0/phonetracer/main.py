def run():
    print("""
        PhoneTracer v2.3
        ----------------
        1. Argument mode
        2. Command-line menu
        3. GUI
        4. Exit
    """)

    choice = input("Choose mode: ").strip()

    if choice == "1":
        from phonetracer import cli_args
        cli_args.run()

    elif choice == "2":
        from phonetracer import cli_menu
        cli_menu.run()

    elif choice == "3":
        from phonetracer import gui_app
        gui_app.run()

    else:
        print("Exiting")


if __name__ == "__main__":
    run()

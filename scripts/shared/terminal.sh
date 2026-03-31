#!/bin/bash

# Config
TERMINAL="konsole" # konsole, elementary, ghostty

# Terminal function
run_terminal() {

    local working_directory=$1
    local script=$2

    # Init
    local terminal_command=""

    # Konsole
    if [[ $TERMINAL == "konsole" ]]; then
        terminal_command+="konsole --new-tab --workdir=\"$working_directory\""
        [[ -n $script ]] && terminal_command+=" -e \"$script\""

    # Ghostty
    elif [[ $TERMINAL == "ghostty" ]]; then
        terminal_command+="ghostty --working-directory=\"$working_directory\""
        [[ -n $script ]] && terminal_command+=" -e bash -c \"$script; bash\""

    # Elementary
    else
        terminal_command+="io.elementary.terminal -t -w \"$working_directory\""
        [[ -n $script ]] && terminal_command+=" -e \"$script\""
    fi

    # Run
    eval $terminal_command
}

create_script() {

    local pwd=$1

    # Remove first argument and get the rest
    shift
    local command=$*

    # Settings
    local script="/tmp/_doublecmd_shell$RANDOM.sh"

    # Create script
    echo "#!/bin/bash" > $script

    # Set current path
    echo "cd \"$pwd\" " >> $script

    # Run command
    if [[ ! $command =~ "\"" && $SKIP_QUOTES == "" ]]
    then
        command="\"$command\""
    fi
    if [[ "$command" != "\"\"" ]]
    then
        echo "$command" >> $script
    fi

    # Set executable flag
    chmod a+x $script

    echo "$script"
}

# Main
main() {

    local command=$*
    local pwd=`pwd`

    # No command
    if [[ $command == "" ]]
    then
        # Run terminal with the current pwd
        run_terminal "$pwd" ""

    # We have a command
    else

        # Create script
        local script=$(create_script "$pwd" $command)

        # Run terminal
        run_terminal "$pwd" "$script"

        # Remove script
        rm $script
    fi
}

# Run main
main $*
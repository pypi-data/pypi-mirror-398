# Bash completion for dremio CLI

_dremio_completion() {
    local cur prev opts base
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"

    # Main commands
    local commands="catalog profile source space folder table view sql job user role tag wiki grant history favorite --help --version"

    # If we're completing the first argument
    if [ $COMP_CWORD -eq 1 ]; then
        COMPREPLY=( $(compgen -W "${commands}" -- ${cur}) )
        return 0
    fi

    # Get the main command
    local cmd="${COMP_WORDS[1]}"

    case "${cmd}" in
        catalog)
            local subcommands="list get get-by-path"
            COMPREPLY=( $(compgen -W "${subcommands}" -- ${cur}) )
            ;;
        profile)
            local subcommands="create list get set-default delete"
            COMPREPLY=( $(compgen -W "${subcommands}" -- ${cur}) )
            ;;
        source)
            local subcommands="list get create update refresh delete test-connection"
            COMPREPLY=( $(compgen -W "${subcommands}" -- ${cur}) )
            ;;
        space)
            local subcommands="create list get delete"
            COMPREPLY=( $(compgen -W "${subcommands}" -- ${cur}) )
            ;;
        folder)
            local subcommands="create list get get-by-path delete"
            COMPREPLY=( $(compgen -W "${subcommands}" -- ${cur}) )
            ;;
        table)
            local subcommands="promote format update"
            COMPREPLY=( $(compgen -W "${subcommands}" -- ${cur}) )
            ;;
        view)
            local subcommands="create list get get-by-path update delete"
            COMPREPLY=( $(compgen -W "${subcommands}" -- ${cur}) )
            ;;
        sql)
            local subcommands="execute explain validate"
            COMPREPLY=( $(compgen -W "${subcommands}" -- ${cur}) )
            ;;
        job)
            local subcommands="list get results cancel profile reflections"
            COMPREPLY=( $(compgen -W "${subcommands}" -- ${cur}) )
            ;;
        user)
            local subcommands="list get create update delete"
            COMPREPLY=( $(compgen -W "${subcommands}" -- ${cur}) )
            ;;
        role)
            local subcommands="list get create update delete add-member remove-member"
            COMPREPLY=( $(compgen -W "${subcommands}" -- ${cur}) )
            ;;
        tag)
            local subcommands="set get delete"
            COMPREPLY=( $(compgen -W "${subcommands}" -- ${cur}) )
            ;;
        wiki)
            local subcommands="set get delete"
            COMPREPLY=( $(compgen -W "${subcommands}" -- ${cur}) )
            ;;
        grant)
            local subcommands="list add remove set"
            COMPREPLY=( $(compgen -W "${subcommands}" -- ${cur}) )
            ;;
        history)
            local subcommands="list run clear"
            COMPREPLY=( $(compgen -W "${subcommands}" -- ${cur}) )
            ;;
        favorite)
            local subcommands="add list run delete"
            COMPREPLY=( $(compgen -W "${subcommands}" -- ${cur}) )
            ;;
    esac
}

complete -F _dremio_completion dremio

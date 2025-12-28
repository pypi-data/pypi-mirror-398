#compdef dremio

_dremio() {
    local -a commands
    commands=(
        'catalog:Catalog operations'
        'profile:Profile management'
        'source:Source management'
        'space:Space management'
        'folder:Folder management'
        'table:Table operations'
        'view:View management'
        'sql:SQL operations'
        'job:Job management'
        'user:User management'
        'role:Role management'
        'tag:Tag management'
        'wiki:Wiki management'
        'grant:Grant management'
        'history:Query history'
        'favorite:Favorite queries'
    )

    local -a catalog_commands
    catalog_commands=(
        'list:List catalog items'
        'get:Get catalog item'
        'get-by-path:Get item by path'
    )

    local -a profile_commands
    profile_commands=(
        'create:Create profile'
        'list:List profiles'
        'get:Get profile'
        'set-default:Set default profile'
        'delete:Delete profile'
    )

    local -a source_commands
    source_commands=(
        'list:List sources'
        'get:Get source'
        'create:Create source'
        'update:Update source'
        'refresh:Refresh source'
        'delete:Delete source'
        'test-connection:Test connection'
    )

    local -a history_commands
    history_commands=(
        'list:List history'
        'run:Run from history'
        'clear:Clear history'
    )

    local -a favorite_commands
    favorite_commands=(
        'add:Add favorite'
        'list:List favorites'
        'run:Run favorite'
        'delete:Delete favorite'
    )

    if (( CURRENT == 2 )); then
        _describe 'command' commands
    elif (( CURRENT == 3 )); then
        case "$words[2]" in
            catalog)
                _describe 'subcommand' catalog_commands
                ;;
            profile)
                _describe 'subcommand' profile_commands
                ;;
            source)
                _describe 'subcommand' source_commands
                ;;
            history)
                _describe 'subcommand' history_commands
                ;;
            favorite)
                _describe 'subcommand' favorite_commands
                ;;
        esac
    fi
}

_dremio "$@"

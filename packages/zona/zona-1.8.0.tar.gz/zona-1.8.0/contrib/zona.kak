# Author: Daniel Fichtinger
# License: BSD-3

# This plugin provides an integration with the Zona static site generator.

provide-module zona %~
    # utility commands for writing blog posts with zona

    ## begin public options
    declare-option -docstring %{
        URL of the zona server.
    } \
    str zona_url "http://localhost:8000"

    declare-option -docstring %{
        Full path to the zona project.
    } \
    str zona_path "/home/fic/dev/ficd.sh"

    declare-option -docstring %{
        Command to call zona.
    } \
    str zona_cmd "zona"

    declare-option -docstring %{
        Command to open URL.
    } \
    str zona_url_cmd "firefox"
    ## end public options

    declare-option -hidden int zona_pid 0

    define-command -docstring %{
        Open the current page in browser.
        -delay switch waits for 1 second before opening.
    } \
    -params 0..1 zona-open %{
        nop %sh{
            {
            	if [ "$1" = '-delay' ]; then
            		sleep 1
            	fi
            	url="$kak_opt_zona_url"
            	case "$kak_buffile" in
            	*/content/*.md | */content/*.html)
            		rel="${kak_buffile#*/content/}"
            		rel="${rel%.md}"
            		rel="${rel%.html}"
            		case "$rel" in
            		*/index) rel="${rel%/index}" ;;
            		index) rel="" ;;
            		esac
            		url="${url}/${rel}"
            		;;
            	esac
            	"$kak_opt_zona_url_cmd" "$url"
            } >/dev/null 2>&1 </dev/null &
        }
    }

    define-command -docstring %{
        Start the preview server.
    } \
    zona-start-preview %{
        try %{
            evaluate-commands %sh{
                cd "$kak_opt_zona_path" || exit 1
                {
                	exec "$kak_opt_zona_cmd" serve
                } >/dev/null 2>&1 </dev/null &
                pid="$!"
                printf 'echo -debug zona pid: "%s"\n' "$pid"
                printf 'set-option global zona_pid %s\n' "$pid"
                echo "zona-open -delay"
            }
            hook global KakEnd .* %{
                try %{
                    zona-stop-preview
                }
            }
        } catch %{
            fail 'Failed to start server:' %val{error}
        }
    }

    define-command -docstring %{
        Stop the preview server.
    } \
    zona-stop-preview %{
        evaluate-commands %sh{
            if [ "$kak_opt_zona_pid" -eq 0 ]; then
            	echo "fail Zona is not currently running!"
            	exit 1
            fi
            if kill -0 "$kak_opt_zona_pid" 2>/dev/null; then
            	kill "$kak_opt_zona_pid"
            	printf 'set-option global zona_pid 0\n'
            else
            	printf 'fail Process %s does not exist' "$kak_opt_zona_pid"
            fi
        }
    }

    define-command -docstring %{
        Set the frontmatter date to today's date.
    } zona-date %{
        evaluate-commands -draft -save-regs | %{
            try %{
                set-register | "date -d '%arg{@}' '+%%Y-%%m-%%d' | tr -d '\n'"
                execute-keys '%s^---.+^date:.+---$<ret><a-s><a-k>^date:<ret>s: \K.+$<ret>'
                execute-keys '|<ret>'
            } catch %{
                fail 'No date in frontmatter!'
            }
        }
    }

~

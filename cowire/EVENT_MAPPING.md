# Cowrie event mapping

Ruta del log JSON:
`/cowrie/cowrie-git/var/log/cowrie/cowrie.json`

## Eventos iniciales seleccionados para Trapnet

### cowrie.session.connect
Mapeo:
- event_source: cowrie
- event_type: session_started

### cowrie.login.success
Mapeo:
- event_source: cowrie
- event_type: ssh_login_attempt
- username
- password
- success = true

### cowrie.command.input
Mapeo:
- event_source: cowrie
- event_type: ssh_command_input
- command = input

### cowrie.command.failed
Mapeo:
- event_source: cowrie
- event_type: ssh_command_failed
- command = input

### cowrie.session.closed
Mapeo:
- event_source: cowrie
- event_type: session_closed
- duration
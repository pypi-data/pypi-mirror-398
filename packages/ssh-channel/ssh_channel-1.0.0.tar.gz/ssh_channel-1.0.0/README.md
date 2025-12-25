# ssh-channel
Send data back through an ssh connection through escape codes.

## Installation
You can install `ssh-channel` with pipx.

```
pipx install ssh-channel
```

## Usage
Wrap your ssh session (or your bash session) with `ssh-channel-receive`

```
ssh-channel-receive ssh server
```

In `~/.config/ssh-channel.conf` add a handler command like so:

```
message:cat > /tmp/message
```

Then will ssh is running you can can run:
```
echo hello | ssh-channel-send message
```











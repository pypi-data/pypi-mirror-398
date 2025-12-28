# ssh-copy-id-via
**@readwithai** - [X](https://x.com/readwithai) - [blog](https://readwithai.substack.com/) - [machine-aided reading](https://www.reddit.com/r/machineAidedReading/) - [📖](https://readwithai.substack.com/p/what-is-reading-broadly-defined)[⚡️](https://readwithai.substack.com/s/technical-miscellany)[🖋️](https://readwithai.substack.com/p/note-taking-with-obsidian-much-of)

I like to use passwordless users on a server as a means of isolation. ssh-copy-id only works if you have a password. This logs in with another user and copy's the ID.

Warning: this is vibe coded. It will likely become less so if I improve it.

## Installation
You can install this with pipx;

```
pipx install ssh-copy-id-via
```

## Usage
This command will log in to server using user and then user it to allow you to login to ssh-user@server.

```
ssh-copy-id-via user@server ssh-user
```

## About me
I am **@readwithai**. I create tools for reading, research and agency sometimes using the markdown editor [Obsidian](https://readwithai.substack.com/p/what-exactly-is-obsidian).

I also create a [stream of tools](https://readwithai.substack.com/p/my-productivity-tools) that are related to carrying out my work. You may be interested in some of these tools.

I write about lots of things - including tools like this - on [X](https://x.com/readwithai).
My [blog](https://readwithai.substack.com/) is more about reading and research and agency.



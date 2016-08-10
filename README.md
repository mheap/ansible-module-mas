Welcome to the beginning of an Ansible module for installing applications via the Mac app store.

To use this module, you'll need `mas` installed (see https://github.com/argon/mas). You can use `homebrew`

```
brew install mas
```

So far, this module has only been tested with the `test-module` script. It needs lots of work both for the module definition and the underling `Mas` class that powers it all

```code
ansible/hacking/test-module -m ./mas.py -a "state=present name=Caffeine"
```

# Help!

There's a fairly big limitation with `mas` in that you need to provide an application ID to install it, not the application name.
For now, there's a hardcoded list of apps that I'm using for testing. Eventually this could be a config file that ships with the module.

However, there's new applications being shipped every day. Does anyone have an idea how to make working with names rather than IDs easier?

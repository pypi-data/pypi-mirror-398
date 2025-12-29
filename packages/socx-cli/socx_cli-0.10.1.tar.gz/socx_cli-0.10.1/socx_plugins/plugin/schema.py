from textwrap import dedent


schema = dedent(r"""
# Required - this will cause the definitions below to be merged into the
# current `plugins` configuration.
plugins:

    # Required - define a new plugin called "my_plugin". It can be invoked
    # later by running `socx my_plugin` in a terminal
    my_plugin:

        # Optional - Define variables `FOO`, `BAR`, and `bazz` in the new
        # subprocess environment where the plugin is invoked.
        env:
            FOO: "VALUE"
            BAR: "VALUE1/VALUE2"
            bazz: "value3:value4:value5"

        # Optional - do/do-not copy environment variables from the environment
        # of the current process into the plugin's subprocess.
        #
        # The default value is false, which means to copy the variables from
        # the current environment instead of using a fresh one.
        fresh_env: true

        # Required - this is later translated into something like:
        #
        #   def my_plugin():
        #       from my_package.my_subpackage import my_function
        #       tmp = sys.argv.pop(0)
        #       try:
        #           rv = my_function()
        #       finally:
        #           sys.argv.insert(0, tmp)
        #       return rv
        command: my_package.my_subpackage:my_function

        # Optional - enable/disable the plugin, this is true by default.
        enabled: true

        # Optional - will place command in a separate panel in the parent
        # command's help menu with a custom "Plugin Commands" title.
        panel: Plugin Commands

        # Optional - additional aliases/shortcuts to set that can be used
        # to invoke the sub-command, in addition to the current name
        # 'my_command' defined at the top of this snippet.
        aliases:
        - my_cmd
        - myc

        # Optional - a short version of the help text that will be used to
        # render the one-liner help text in the parent command's help menu
        short_help: |
            My short one-liner help text.

        # Optional - help text shown at the bottom/end of the help menu.
        #
        # This is usually usful for providing references, such as a url to
        # a documentation site.
        epilog: |
            Visit [link]https://my_awesome_website.com/documentation[/link]
            for additional info about 'my_plugin'.

        # Optional - plugin help text to show when running the command
        # with the -h or --help flag.
        #
        # Note that markdown is supported, and is the recommended format
        # for documenting plugin commands.
        #
        # To see an example for how markdown is later rendered in the
        # terminal, check out the GIF image for the `socx git help`
        # command in the quickstart section.
        help: |
            # My Plugin

            My longer descriptive and helpful help text.

            ## My Plugin Subtitle

            **Lorem Ipsum** - Lorem ipsum dolor sit amet, consectetur
            adipiscing elit.

            Aenean laoreet faucibus tincidunt. Integer nec magna at nunc
            posuere tincidunt.

            > ---
            > ***TIP***:
            >
            > Class aptent taciti sociosqu ad litora torquent per conubia
            > nostra, per inceptos himenaeos. Cras sollicitudin et massa
            > in efficitur.
            >
            > ---

""").strip()

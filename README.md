# Generate compile_commands.json

Requires python and make.

It works by running make in dry-mode to get the output of commands.

It will detect compiler used in `$CC` env variable and fallbacks to `gcc` or `gpp` if env variable is not set.

Should work with any C/C++ project that incorporates make for build system. CMake has generation of compile_commands.json integrated.

### Usage

It registers command `:GenCompileCommands` and mapping in normal mode to `<leader>lg`.

## Lazyvim
```lua
return {
    'FLeWz/gen-compile-commands.vim',
    version = false,
    config = function()
        require('gen-compile-commands')
    end,
}
```

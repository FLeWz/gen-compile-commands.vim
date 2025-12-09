local M = {}

local function get_script_path()
	local lua_source  = debug.getinfo(1, "S").source
	local lua_path    = lua_source:sub(2)
	local lua_dir     = vim.fn.fnamemodify(lua_path, ':h')
	local script_path = lua_dir .. '/../../python/gen-compile-commands.py'
	-- Resolve any relative parts (../) to an absolute path
	return vim.fn.fnamemodify(script_path, ':p')
end

function M.run_python_script()
	local script = get_script_path()
	local cwd = vim.fn.getcwd()
	local output_buf = {}

	vim.fn.jobstart({ 'python3', script }, {
		cwd = cwd,
		stdout_buffered = true,
		stderr_buffered = true,
		on_stdout = function(_, data, _)
			if data then
				for _, line in ipairs(data) do
					table.insert(output_buf, line)
				end
			end
		end,
		on_stderr = function(_, data, _)
			if data then
				for _, line in ipairs(data) do
					table.insert(output_buf, line)
				end
			end
		end,
		on_exit = function(_, code, _)
			if code ~= 0 then
				vim.api.nvim_err_writeln('[GenCompileCommands] Python script exited with code ' .. code)
			else
				local full_output = table.concat(output_buf, "\n")
				vim.notify(full_output, vim.log.levels.INFO, { title = "GenCompileCommands", timeout = 8000 })
			end
		end,
	})
end

vim.api.nvim_create_user_command('GenCompileCommands', function()
	M.run_python_script()
end, { nargs = 0 })

vim.api.nvim_set_keymap('n', '<leader>lg', ':GenCompileCommands<CR>',
	{ noremap = true, silent = true, desc = 'Generate compile_commands.json' })

return M

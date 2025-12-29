# Install
The first thing is to install Claude Code and Stata-MCP.  
Claude Code starts with `npm` command, and Stata-MCP is start with `uvx` or `python3.11+`, so we should install npm and uvx.

## Preparation
### brew
I recommend to use `brew` to install them, run the following command in your terminal to install brew, if you want to know more information about brew, you can visit [Homebrew](https://brew.sh/).
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Then, use the following command to check whether install it successfully.
```bash
brew --version
```

### nvm, node and npm
`nvm` is a Node Version Manager, it can help you to manage different Node versions.  
`node` is a JavaScript runtime environment. It can help you to manage different Node versions.  
`npm` is a package manager for Node. It can help you to manage different Node versions.

You can install nvm directly with `brew install`
```bash
brew install nvm
```

Then, you should add the following lines to your `~/.zshrc` file
```bash
echo 'export NVM_DIR="$HOME/.nvm"' >> ~/.zshrc
echo '[ -s "/opt/homebrew/opt/nvm/nvm.sh" ] && . "/opt/homebrew/opt/nvm/nvm.sh"' >> ~/.zshrc
source ~/.zshrc
```

Check the status of nvm:
```bash
nvm --version
```

Then, you can install node with nvm:
```bash
nvm install 20.19.5  # At least you should install 18+ 
nvm alias default 20
nvm use default
node -v
npm -v
```

### uvx
As macOS has a build-in python, but we always need a newer version or independent version of python, so we should install `uv`, as the official documents, they provide a command for install it, or you can install it with `brew`, more over you can install with `pip`. (b and c pasted from the official documents)

a. Install uvx with `brew`
```bash
brew install uvx
uvx --version
```

b. Install uvx from astral.sh
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

If your system doesn't have `curl`, you can use `wget`:
```bash
wget -qO- https://astral.sh/uv/install.sh | sh
```

c. Install uvx from pypi
If installing from PyPI, we recommend installing uv into an isolated environment, e.g., with pipx:
```bash
pipx install uv
```

However, pip can also be used:
```bash
pip install uv
```
> Note: uv ships with prebuilt distributions (wheels) for many platforms; if a wheel is not available for a given platform, uv will be built from source, which requires a Rust toolchain. See the contributing setup guide for details on building uv from source.

## Claude Code
Now, we can install Claude Code. Run the following command in your terminal to install Claude Code.
```bash
npm install -g @anthropic-ai/claude-code
```

> Install from brew is also available, but it is still in beta.
> ```bash
> brew install --cask claude-code
> ```

Then, you can use `claude` in any terminal to start Claude Code, you can enjoy it now.

## Stata-MCP
Stata-MCP will be one of the tool in your Claude Code, so we should install it in Claude Code, it is more easy to install it.
```bash
export STATA_MCP_CWD=$(pwd)
claude mcp add stata-mcp uvx stata-mcp
```

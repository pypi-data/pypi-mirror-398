# uv
uv is one of the most popular tools for managing your python projects, you can find the official documents on [GitHub](https://github.com/astral-sh/uv).

Given that there is a lot of user is Chinese, it is difficult to reach the pypi (limitation of the web speed), here is a short introduction for change the source to pypi.org.

The following is sourcing from [Tsinghua University Mirror](https://mirror.tuna.tsinghua.edu.cn/help/pypi/).

Edit your `~/.config/uv/uv.toml` or `/etc/uv/uv.toml` file with the following content:
```toml
[[index]]
url = "https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple/"
default = true
```

If you want to edit the file, you maybe need use `sudo`, here is a simple way to edit the file without `sudo` (on macOS and Linux with `nano` command, Windows user should find your own way to edit the file):
```bash
sudo nano /etc/uv/uv.toml
# <ENTER YOUR COMPUTER PASSWORD>
# AFTER edit, type control+x to exit
cat /etc/uv/uv.toml  # to find out whether it is saved.
```


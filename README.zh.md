[English](README.md) | [Chinese](README.zh.md)

## 实现的功能

可拓展的类似301跳转的网页一键部署

注意：最好在一台全新的机器安装此程序，此程序会自动部署环境并引导用户输入期望引导跳转的域名，和跳转的目标域名，类似实现用户输入`aaa.com`，跳转至用户期望的`bbb.com`，`aaa.com` 的域必须是用户自有的。

## 使用方法

1. 首先克隆本仓库
   `git clone https://github.com/Catchabox/redirecting-page.git`

2. 给予程序执行权限
   `chmod +x *`

3. 首先执行`env`自动部署环境
   `./env`
   程序会自动安装nginx和PHP-FPM

4. 将域名`aaa.com`解析到你的机器
   `A    X.X.X.X`

5. 再次执行部署跳转程序
   `./install`

   程序会自动申请证书，自动部署网页

   注意事项：如果本地已经存在PHP环境有可能被覆盖，所以推荐使用没有安装过PHP和nginx的机器进行安装部署，当然后续会出Docker版本来规避这个问题，如果你想取消掉刚刚的跳转，你可以执行`./uninstall`来进行卸载刚刚部署好的页面，同时删除刚刚申请的证书

6. 如果你想修改刚刚跳转的页面，比如刚刚是`aaa.com -> bbb.com`现在想修改为`aaa.com -> ccc.com`那么你可以通过`aaa.com/edit.html`进行修改，密码是`upadte.php`文件内写死的，默认是`XXXXXXX`强烈建议修改


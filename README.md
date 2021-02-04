# CowtransferAPI
https://cowtransfer.com 奶牛快传的第三方api  
**简洁的api静默模式**  
**美观的命令行模式**  
还在制作中  
隔壁go语言→[传送门](https://github.com/Mikubill/cowtransfer-uploader)
# 图片  
![上传文件](https://www.helloimg.com/images/2021/02/04/upload100-00-00--00-00-3014d32e1205ca6c0d.gif)
![上传文件](https://www.helloimg.com/images/2021/02/04/upload295b7a0aad835c67.png "上传文件")  
# 快速使用
- 此包需要 Python 3.6 或更新版本。
- `pip install PicImageSearch`
- 或者 `pip install PicImageSearch -i https://pypi.tuna.tsinghua.edu.cn/simple`
```
#命令行模式
 python -m CowtransferAPI upload C:\Users\kuluj\Downloads\PCQQ2020.exe
#python -m CowtransferAPI upload [文件地址]
```
# TODO
- 美化
  - [x] 彩色输出
  - 格式输出
      - [x] 字典dict
      - [x] 表格
      - [x] 列
      - [x] 分隔符
  - [x] 进度条展示
  - ~~全动态输出~~**（由于与进度条不能共存，已被遗弃(ps:要是有人会请务必教我)）**
  - [x] 详细日志报告
- [x] 命令行调用
- 上传
    - [x] 单文件上传
    - [ ] 多文件上传
    - [ ] 文件夹上传
- 下载
    - [ ] 单文件下载
    - [ ] 多文件下载
    - [ ] 文件夹下载
- [ ] 异步
- [ ] 多线程
- 小功能
    - [ ] Hash检验
    - [ ] 更多用户操作
    - [x] 静默下载
    - [ ] 日志生成
    - [ ] 记住设置
    - [ ] 二维码取件
    - [ ] 傻瓜化提示
    - [ ] 
    - [ ]
    - [ ]
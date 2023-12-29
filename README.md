# Nastools
针对nastools一些功能进行更新优化，自用



## 功能优化改善

1. 修复bug：
   
   (1)识别词替换中不能使用正则匹配（通过识别标记开启正则匹配）-已完成
   
   实现效果：
   
   ![image-20230831134913874](https://raw.githubusercontent.com/miraclemie/pifgo/main/202308311349996.png)
   
   原文件名：`[ANi] 文豪野犬 第五季 - 01 [1080P][Baha][WEB-DL][AAC AVC][CHT].mp4`
   
   新文件名：`[ANi] 文豪野犬_S01 - 50 [1080P][Baha][WEB-DL][AAC AVC][CHT].mp4`
   
   ![image-20230831135952958](https://raw.githubusercontent.com/miraclemie/pifgo/main/202308311359056.png)
   
   (2)解决了豆瓣api中不能同步收藏数据问题
   
   
   
1. 目前进度：
   
   (1)已优化普通视频文件识别、转移目录的逻辑，解决文件名中因文件md5编码会识别错误集数的问题，适应90%视频的识别，其余10%需要自添加自定义识别词来增强识别，其中自定义识别词中的“[]、【】、（）、()”等符号需要加`\`进行转义，也可以直接使用名称，不加符号
   
   ![image-20231227084330832](https://raw.githubusercontent.com/miraclemie/pifgo/main/202312270843241.png)
   
   (2)已新增临时文件夹的目录的手动规整规范性目录的file_helper底层代码编写
   
   (3)打算增加is_anime的逻辑判断，多利用anitopy库对anime进行文件识别


3. 打算新增的功能：

   - file_helper主要针对那种tmdb和豆瓣信息对anime每季信息不统一以及集数标号不是顺序排列的问题，比如精灵宝可梦、海贼王等，进行对每季的集数重新编排（根据目录文件的集数从小到大的顺序进行从1到xx进行重命名），会在前端中增加这个模块（持续中）
   - 新增国内比较多的字幕组和其他的bt站的bt下载爬取适配，增加索引源
   - 新增下载工具-百度云的转存适配，配合群晖的cloud sync的转存目录进行下载到对应的目录



## 修改思路

### 1、新增btbt站点的下载订阅（自定义订阅）：

**解决方案：**

**通过nastools的api接口：`/api/v1/rss/update`进行新增或修改自定义订阅**

**触发条件：**

**通过豆瓣订阅触发后没有订阅到返回结果，从而返回一个tag变量传到触发**

**细节：**

- 需要自建的rsshub的订阅（前端页面上需要新增一个输入，后端在config.yaml中加）
- 需要考虑rss订阅domain后缀需要域名是否能访问通


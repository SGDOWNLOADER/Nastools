# Nastools
针对nastools一些功能进行更新优化，自用



## 功能优化改善

1. 修复bug：
   (1)识别词替换中不能使用正则匹配（通过识别标记开启正则匹配）-已完成

   ![image-20230814084707670](https://picgomie.oss-cn-beijing.aliyuncs.com/202308140847072.png)

   实现效果：

   ![image-20230831134913874](https://raw.githubusercontent.com/miraclemie/pifgo/main/202308311349996.png)

   原文件名：`[ANi] 文豪野犬 第五季 - 01 [1080P][Baha][WEB-DL][AAC AVC][CHT].mp4`

   新文件名：`[ANi] 文豪野犬_S01 - 50 [1080P][Baha][WEB-DL][AAC AVC][CHT].mp4`

   ![image-20230831135952958](https://raw.githubusercontent.com/miraclemie/pifgo/main/202308311359056.png)
   
   (2)解决了豆瓣api中不能同步收藏数据问题
   
   (3)解决了文件大量转移到目录后，会存在识别错误(待观察)


3. 打算新增的功能：

   - 工具下载其他文件后，字幕组的bt文件存在和tmdb里面的剧集命名不规范的，比如海贼王等，需要手动整理到临时文件夹中，再通过程序自动规整后再进行识别分类（自动化）
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


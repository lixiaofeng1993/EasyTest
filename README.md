<div id="cnblogs_post_body" class="blogpost-body"><p>&nbsp;</p>
<p>　　下载了大神的EasyTest项目demo修改了下&lt;https://testerhome.com/topics/12648 原地址&gt;。也有看另一位大神的HttpRunnerManager&lt;https://github.com/HttpRunner/HttpRunnerManager 原地址&gt;，由于水平有限，感觉有点复杂~~~</p>
<p>&nbsp;</p>
<p>修改内容</p>
<p>　　1.增加了页面级的redis缓存；</p>
<p>　　2.完善了项目、环境、接口、用例、计划、签名的编辑和删除功能；</p>
<p>　　3.签名简单的实现了md5加密和AES算法加密；</p>
<p><img src="https://img2018.cnblogs.com/blog/1160412/201905/1160412-20190519170047622-990232023.png" alt=""></p>
<p>&nbsp;</p>
<p>　　4.增加接口批量导入功能；</p>
<p><img src="https://img2018.cnblogs.com/blog/1160412/201905/1160412-20190519165923178-1862125022.png" alt=""></p>
<p>&nbsp;</p>
<p>　　5.测试报告优化及日志查看&lt;报告借鉴 BeautifulReport 页面 https://github.com/TesterlifeRaymond/BeautifulReport&nbsp; 原地址&gt;。注：饼图是用 plt 生成的一张图片；</p>
<p><img src="https://img2018.cnblogs.com/blog/1160412/201905/1160412-20190519170324760-626895314.png" alt=""></p>
<p><img src="https://img2018.cnblogs.com/blog/1160412/201907/1160412-20190701172010127-1278836658.png" alt=""></p>
<p>&nbsp;</p>
<p><img src="https://img2018.cnblogs.com/blog/1160412/201905/1160412-20190519170809044-214784247.png" alt="">&nbsp;　　</p>
<p>　　　　及查看全部日志</p>
<p><img src="https://img2018.cnblogs.com/blog/1160412/201905/1160412-20190519170843997-404612699.png" alt=""></p>
<p>&nbsp;</p>
<p>&nbsp;　　</p>
<p>　　6.定时任务，celery实现；定时任务运行失败后，会发送邮件提醒；</p>
<p>&nbsp;</p>
<p><img src="https://img2018.cnblogs.com/blog/1160412/201907/1160412-20190701172110015-506484207.png" alt=""></p>
<p>　　添加定时任务走的是admin站点页面</p>
<p><img src="https://img2018.cnblogs.com/blog/1160412/201905/1160412-20190504204750175-1383782729.png" alt=""></p>
<p>　　flower实现任务监控</p>
<p><img src="https://img2018.cnblogs.com/blog/1160412/201907/1160412-20190701172232140-934604829.png" alt=""></p>
<p>&nbsp;</p>
<p>　　7.locust集成到平台中；</p>
<p><img src="https://img2018.cnblogs.com/blog/1160412/201905/1160412-20190519171203847-626395283.png" alt=""></p>
<p>　　定时任务和性能测试根据测试计划中的is_task、is_locust来判断；</p>
<p><img src="https://img2018.cnblogs.com/blog/1160412/201905/1160412-20190519171341195-178890610.png" alt=""></p>
<p>&nbsp;</p>
<p>　　8.简单的首页展示；</p>
<p><img src="https://img2018.cnblogs.com/blog/1160412/201907/1160412-20190701172327160-801185610.png" alt=""></p>

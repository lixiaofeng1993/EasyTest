<div id="cnblogs_post_body" class="blogpost-body"><p>&nbsp;</p>
<p>&nbsp;</p>
<p>　　下载了大神的EasyTest项目demo修改了下&lt;https://testerhome.com/topics/12648 原地址&gt;。也有看另一位大神的HttpRunnerManager&lt;https://github.com/HttpRunner/HttpRunnerManager 原地址&gt;，由于水平有限，感觉有点复杂~~~</p>
<p>&nbsp;1.登录页面</p>
<p><img src="https://img2018.cnblogs.com/blog/1160412/201907/1160412-20190702141820759-1065366379.png" alt=""></p>
<p>&nbsp;</p>
<p>2.首页</p>
<p><img src="https://img2018.cnblogs.com/blog/1160412/201907/1160412-20190702141938977-908661687.png" alt=""></p>
<p>&nbsp;</p>
<p>3.项目管理</p>
<p><img src="https://img2018.cnblogs.com/blog/1160412/201907/1160412-20190702142937052-697000207.png" alt=""></p>
<p>&nbsp;</p>
<p>4.测试环境</p>
<p><img src="https://img2018.cnblogs.com/blog/1160412/201907/1160412-20190702143021902-1550744781.png" alt=""></p>
<p>&nbsp;</p>
<p>　　1&gt;设置headers；可以每个url设置共同的header，可以存在变量；执行时，指定接口补全header；</p>
<p>　　<img src="https://img2018.cnblogs.com/blog/1160412/201907/1160412-20190701180204197-1071198251.png" alt=""></p>
<p>&nbsp;　　</p>
<p>5.接口管理</p>
<p><img src="https://img2018.cnblogs.com/blog/1160412/201907/1160412-20190702143212890-1708850484.png" alt=""></p>
<p>　　1&gt;swagger导入功能；根据指定的测试环境url，导入swagger接口数据到平台中；</p>
<p>&nbsp;</p>
<p>6.用例管理</p>
<p>　　选择测试环境，进行单个接口调试，多个接口模拟业务场景执行；</p>
<p><img src="https://img2018.cnblogs.com/blog/1160412/201907/1160412-20190702143624770-1599818900.png" alt=""></p>
<p>&nbsp;</p>
<p><img src="https://img2018.cnblogs.com/blog/1160412/201907/1160412-20190701181016768-2035628145.png" alt=""></p>
<p>&nbsp;</p>
<p>7.测试计划</p>
<p>　　选择用例，组合执行；生成测试报告；</p>
<p><img src="https://img2018.cnblogs.com/blog/1160412/201907/1160412-20190702144004174-661122280.png" alt=""></p>
<p>&nbsp;</p>
<p>8.定时任务</p>
<p><img src="https://img2018.cnblogs.com/blog/1160412/201907/1160412-20190702144058401-1501422093.png" alt=""></p>
<p>&nbsp;</p>
<p>　　flower 实现任务监控；增加 BackTask 按钮，返回测试平台；</p>
<p><img src="https://img2018.cnblogs.com/blog/1160412/201907/1160412-20190701181426348-1861485776.png" alt=""></p>
<p>9.运行报告</p>
<p><img src="https://img2018.cnblogs.com/blog/1160412/201907/1160412-20190702144135587-1658666127.png" alt=""></p>
<p>&nbsp;</p>
<p>　　接口测试报告</p>
<p><img src="https://img2018.cnblogs.com/blog/1160412/201907/1160412-20190701181613297-499086621.png" alt=""></p>
<p>10.性能测试</p>
<p>　　集成locsut，指定测试计划进行性能测试；</p>
<p><img src="https://img2018.cnblogs.com/blog/1160412/201907/1160412-20190702144208723-1195827989.png" alt=""></p>
<p>&nbsp;</p>
<p>11.签名方式</p>
<p>　　支持接口md5、AES算法加密和用户认证；</p>
<p><img src="https://img2018.cnblogs.com/blog/1160412/201907/1160412-20190702144237400-1855999016.png" alt=""></p>
<p>&nbsp;</p>
<p>12.用户管理</p>
<p><img src="https://img2018.cnblogs.com/blog/1160412/201907/1160412-20190702144302413-2071835935.png" alt=""></p>
<p>&nbsp;</p>
<p>&nbsp;13.后台管理</p>
<p><img src="https://img2018.cnblogs.com/blog/1160412/201907/1160412-20190702144547067-1776196840.png" alt=""></p>
<p><img src="https://img2018.cnblogs.com/blog/1160412/201907/1160412-20190702144627178-151583365.png" alt=""></p>
<p>&nbsp;</p>
<p>&nbsp;</p>
<p>接口传参：</p>
<p>　　1.不同接口要提取的参数相同：使用接口路径和提取参数拼接；</p>
<p>　　<img src="https://img2018.cnblogs.com/blog/1160412/201907/1160412-20190706015447043-54413354.png" alt=""></p>
<p>　　<img src="https://img2018.cnblogs.com/blog/1160412/201907/1160412-20190706015627142-220431991.png" alt=""></p>
<p>　　2.接口中参数相同，提取指定某个：一般接口返回值中是list，才会存在要提取的参数有多个相同的情况，所有使用角标&lt;第几个&gt;来区分；</p>
<p>　　<img src="https://img2018.cnblogs.com/blog/1160412/201907/1160412-20190706020256925-432748156.png" alt=""></p>
<p>　　<img src="https://img2018.cnblogs.com/blog/1160412/201907/1160412-20190706020340788-1052423683.png" alt=""></p>
<p>&nbsp;　　3.从一个接口中同时提取多个参数；</p>
<p>　　<img src="https://img2018.cnblogs.com/blog/1160412/201907/1160412-20190707200403620-1101545172.png" alt=""></p>
<p>&nbsp;</p>
</div>
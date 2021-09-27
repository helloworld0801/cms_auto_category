# cms_auto_category
cms category自动化更新，支持帝国cms和phpcms

# 简介
因为运营的无脑需求，想要实现栏目页自动更新。  
php语言虽然可以做到，但太麻烦复杂了。  
此功能通过python+selenium，通过chrome自动化实现。  

# 部署
我用的是python V3.9。python2没做兼容，肯定会有些地方会报错。  
只运行在**window环境**下  
如果需要打包成exe文件，通过`pyinstaller --onefile main.spec`来打包  
需要自己安装好*谷歌浏览器*，谷歌驱动会自己下载安装好对应的版本  

# 注意事项
1. **web.yaml** 是栏目需要自动更新的站点信息，源码注释都在，大家看着改改就行  

2. **phpcms** 需要在后台登入界面屏蔽掉验证码验证的模块。  
  我的处理方法是在登入地址后面加个参数`ignore=1`来判断是否开启验证码。  
- `admin/index.php`  

  ```
  if (!isset($_GET['card'])) {
    $username = isset($_POST['username']) ? trim($_POST['username']) : showmessage(L('nameerror'),HTTP_REFERER);
    $code = isset($_POST['code']) && trim($_POST['code']) ? trim($_POST['code']) : showmessage(L('input_code'), HTTP_REFERER);
    if ($_SESSION['code'] != strtolower($code)) {
      $_SESSION['code'] = '';
      showmessage(L('code_error'), HTTP_REFERER);
    }
    $_SESSION['code'] = '';
  } else { //口令卡验证
    if (!isset($_SESSION['card_verif']) || $_SESSION['card_verif'] != 1) {
      showmessage(L('your_password_card_is_not_validate'), '?m=admin&c=index&a=public_card');
    }
    $username = $_SESSION['card_username'] ? $_SESSION['card_username'] :  showmessage(L('nameerror'),HTTP_REFERER);
  }
  ```
  修改为
  ```
  if (!isset($_GET['card'])) {
    $username = isset($_POST['username']) ? trim($_POST['username']) : showmessage(L('nameerror'),HTTP_REFERER);
    if (!$_POST['ignore']){
        $code = isset($_POST['code']) && trim($_POST['code']) ? trim($_POST['code']) : showmessage(L('input_code'), HTTP_REFERER);
        if ($_SESSION['code'] != strtolower($code)) {
          $_SESSION['code'] = '';
          showmessage(L('code_error'), HTTP_REFERER);
        }
      }
      $_SESSION['code'] = '';
  } else { //口令卡验证
    if (!isset($_SESSION['card_verif']) || $_SESSION['card_verif'] != 1) {
      showmessage(L('your_password_card_is_not_validate'), '?m=admin&c=index&a=public_card');
    }
    $username = $_SESSION['card_username'] ? $_SESSION['card_username'] :  showmessage(L('nameerror'),HTTP_REFERER);
  }
  ```

- `login.tpl.php` 

  ```
    <?php echo L('security_code')?>：</label><input name="code" type="text" class="ipt ipt_reg" onfocus="document.getElementById('yzm').style.display='block'" />
    <div id="yzm" class="yzm"><?php echo form::checkcode('code_img')?><br /><a href="javascript:document.getElementById('code_img').src='<?php echo SITE_PROTOCOL.SITE_URL.WEB_PATH;?>api.php?op=checkcode&m=admin&c=index&a=checkcode&time='+Math.random();void(0);"><?php echo L('click_change_validate')?></a></div>
  ```
  修改为
  ```
   <?php if (!$_GET['ignore']){ ?>
   <label><?php echo L('security_code')?>：</label><input name="code" type="text" class="ipt ipt_reg" onfocus="document.getElementById('yzm').style.display='block'" />
   <div id="yzm" class="yzm"><?php echo form::checkcode('code_img')?><br /><a href="javascript:document.getElementById('code_img').src='<?php echo SITE_PROTOCOL.SITE_URL.WEB_PATH;?>api.php?op=checkcode&m=admin&c=index&a=checkcode&time='+Math.random();void(0);"><?php echo L('click_change_validate')?></a></div>
   <?php }else{?><input name="ignore" value="1" type="hidden"/><?php }?>
  ```
    
# 之后更新  
增加自动安装google浏览器的功能，要做就做懒人流程。  
再有空就弄弄兼容，但这个优先级很低，如果有新的想法和点子，这个肯定退后，比如说做界面化，哈哈。  

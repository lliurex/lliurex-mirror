function LliurexMirror(){
  this.distros = {'llx16':{}};
  this.activedistro = 'llx16';
  this.progresscolors = {'new':'#4caf50' ,'ok' : '#4caf50' , 'error' : 'red', 'working':'#03A9F4','default':'black'};
  this.bars = {};
  this.edit = null;
  this.progressoptionsdefault = {color:this.progresscolors['ok'], trailcolor:'#9f9f9f', trailWidth:3, strokeWidth: 3, easing: 'easeInOut', text: {value:''}};
  this.intervalupdate = null;
  this.progress = 0;
  this.credentials = [sessionStorage.username , sessionStorage.password];
  this.n4dclass = "MirrorManager";
}

LliurexMirror.prototype.translate = function translate(text){
  return (i18n.gettext("lliurex-mirror", text));
}


LliurexMirror.prototype.loadMirrorInfo = function loadMirrorInfo(info){
  var self = this;
  var availabledistros = Object.keys(this.distros);
  availabledistros.forEach(function load(distro){
    $.extend(self.distros[distro],self.distros[distro],info[distro]);
  });
}

LliurexMirror.prototype.loadProgressBar = function loadProgressBar(container,distro) {
  var self = this;
  var progressoptions = self.progressoptionsdefault;
  var status_mirror = self.distros[distro]['status_mirror'].toLowerCase();
  progressoptions['color'] = self.progresscolors.hasOwnProperty(status_mirror) ? self.progresscolors[status_mirror] : self.progresscolors['default'];  
  progressoptions['text']['value'] = distro;
  self.bars[distro] = new ProgressBar.Circle(container, progressoptions);
  self.bars[distro].animate(1 - (100 - self.distros[distro]['progress']) / 100 );
}

LliurexMirror.prototype.loadOrigin = function loadOrigin(distro){
  var self = this;
  Utils.n4d(self.credentials, self.n4dclass, "get_option_update", [distro], function getoptionupdate(response){
    if(response != null && response['status'] == true){
      Utils.n4d(self.credentials, self.n4dclass, "get_mirror_orig", [distro,response['msg']], function getmirrororig(response){
        if(response != null && response['status'] == true){
          self.distros[distro]['orig'] = response['msg'];
          self.showOrig(response['msg']);
        }
      });
    }
  });
}

LliurexMirror.prototype.showOrig = function showOrig(text){
  $("#llxmirrororig").text(text);
}

LliurexMirror.prototype.bindEvents = function bindEvents(){
  var self = this;
  var distro = self.activedistro;
  $(document).on("moduleLoaded",function(e,args){
  	if (args['moduleName'] != "lliurex-mirror"){
  		return ;
    }
    Utils.n4d('', 'VariablesManager', 'get_variable', ['LLIUREXMIRROR'], function get_variables(response){
      self.loadMirrorInfo(response);
      self.loadProgressBar('#llxmirrorprogress',distro);
      self.loadOrigin(distro);
      self.showArchitecture();
      //self.showMirrorSize();
      self.checkLliurexUpdate();
    });
  });
  $("#llxmirrormenuarch").on('click',function modifyarch(e,args){
    self.showOptionsMenu(self,'#llxmirrormenuarch',self.buildArchMenuConfig);
  });

  $("#llxmirrormenuorig").on('click',function modifyarch(e,args){
    self.showOptionsMenu(self,'#llxmirrormenuorig',self.buildOrigMenuConfig);
  });

  var buttonupdate = document.querySelector("#llxmirrorupdate");
  self._updateMirror = self.updateMirror.bind(self);
  self._stopUpdate = self.stopUpdate.bind(self);
  buttonupdate.addEventListener('click',self._updateMirror,false);
};

LliurexMirror.prototype.showOptionsMenu = function showOptionsMenu(self,menuid,buildfunction){
  var configuration = document.querySelectorAll('#llxmirrorconfiguration')[0];
    if (self.edit != menuid & self.edit != null){
      document.querySelector(self.edit).click();
      setTimeout(function() {document.querySelector(menuid).click();}, 1000);
    }
    else{
      if (configuration.classList.contains('llxmirrordisabled')){
       self.edit = menuid;
       buildfunction.call(self,'#llxmirrorconfigurationcontent');
      }
      else{
       self.edit = null;
      }
      configuration.classList.toggle('llxmirrordisabled');
    }
}

LliurexMirror.prototype.buildArchMenuConfig = function buildArchMenuConfig(idcontainer){
  var self = this;
  var buttonGroups = document.createElement('div');
  var enablei386 = document.createElement('a');
  var enableamd64 = document.createElement('a');
  buttonGroups.classList.add("btn-group","btn-group-justified","btn-group-raised");
  enablei386.classList.add('btn','btn-raised');
  enableamd64.classList.add('btn','btn-raised');

  if (self.architectures.indexOf('i386')>=0){
    enablei386.classList.add('btn-info');
  }
  if (self.architectures.indexOf('amd64')>=0){
    enableamd64.classList.add('btn-info');
  }
  enablei386.innerHTML = "32 Bits";
  function modifyGuiArch(self,barch){
    if (barch.classList.contains('btn-info')){
      barch.classList.remove('btn-info');
    }
    else{
      barch.classList.add('btn-info');
    }
    var archs = [];
    if (enablei386.classList.contains('btn-info')) archs.push('i386');
    if (enableamd64.classList.contains('btn-info')) archs.push('amd64');
    self.setArchitecture(archs);
    self.showArchitecture();
  }
  enablei386.addEventListener('click',function(){
    modifyGuiArch(self,enablei386);
  });
  enableamd64.innerHTML = "64 Bits";
  enableamd64.addEventListener('click',function(){
    modifyGuiArch(self,enableamd64);
  });
  buttonGroups.appendChild(enablei386);
  buttonGroups.appendChild(enableamd64);

  /*
    Clean container
   */
  var container = document.querySelector(idcontainer);
  var fc = container.firstChild;
  while(fc){
    container.removeChild(fc);
    fc=container.firstChild;
  }
  /*
    Load content
   */
  container.appendChild(buttonGroups);
};

LliurexMirror.prototype.buildOrigMenuConfig = function buildOrigMenuConfig(idcontainer){
  var self = this;
  var buttonGroups = document.createElement('div');
  buttonGroups.classList = ["btn-group"];
  buttonGroups.classList.add("btn-group-justified");
  buttonGroups.classList.add("btn-group-raised");
  var internet = document.createElement('a');
  var url = document.createElement('a');
  internet.classList.add('btn');
  url.classList.add('btn');
  internet.classList.add('btn-raised');
  url.classList.add('btn-raised');
  internet.innerHTML = "LliureX.net";
  url.innerHTML = "Custom url";

  buttonGroups.appendChild(internet);
  buttonGroups.appendChild(url);
  

  var customurlform = document.createElement('div');
  customurlform.classList.add('form-group');
  customurlform.classList.add('label-floating');
  customurlform.classList.add('llxmirrorhidden');
  var labelcustomurl = document.createElement('label');
  labelcustomurl.classList.add('control-label');
  labelcustomurl.setAttribute('for','customurl');
  labelcustomurl.innerHTML = 'Write mirror url without http://';
  var inputcustomurl = document.createElement('input');
  var distro = self.activedistro;
  inputcustomurl.classList.add("form-control");
  inputcustomurl.type="text";
  inputcustomurl.id="customurl";
  inputcustomurl.addEventListener('input',function(){
    self.modifyGuiOrig();
  });
  customurlform.appendChild(labelcustomurl);
  customurlform.appendChild(inputcustomurl);

  internet.addEventListener('click',function(){
    if(url.classList.contains('btn-info')){
      url.classList.remove('btn-info');
    }
    if(! internet.classList.contains('btn-info')){
      customurlform.classList.toggle('llxmirrorhidden');
      internet.classList.add('btn-info');
      self.setOrig('1','lliurex.net/xenial');
      self.showOrigin();
    }
  });
  url.addEventListener('click',function(){
    if(internet.classList.contains('btn-info')){
      internet.classList.remove('btn-info');
    }
    if(! url.classList.contains('btn-info')){
      url.classList.add('btn-info');
      customurlform.classList.toggle('llxmirrorhidden');
      self.setOrig('3',customurl.value);
      self.showOrigin();
    }
  });

  Utils.n4d(self.credentials, self.n4dclass, "get_option_update", [distro], function getoptionupdate(response){
    var credentials=[sessionStorage.username , sessionStorage.password];
    var n4dclass="MirrorManager";
    var n4dmethod="get_mirror_orig";
    var arglist=[self.activedistro,response['msg']];
    Utils.n4d(credentials, n4dclass, n4dmethod, arglist, function getmirrororig(response){
      var value = response['msg'];
      if (value.toLowerCase() == 'lliurex.net/xenial'){
        internet.classList.add('btn-info');
      }
      else{
        url.classList.add('btn-info');
        inputcustomurl.value = value;
        customurlform.classList.remove('llxmirrorhidden');
      }
    });
  });

    /*
    Clean container
   */

  var container = document.querySelector(idcontainer);
  var fc = container.firstChild;
  while(fc){
    container.removeChild(fc);
    fc=container.firstChild;
  }
  /*
    Load content
   */
  container.appendChild(buttonGroups);
  container.appendChild(customurlform);
}

LliurexMirror.prototype.modifyGuiOrig = function modifyGuiOrig(){
  var self = this;
  clearTimeout(self.urlorig);
  self.urlorig = setTimeout(function(){
    self.setOrig('3',document.querySelector('#customurl').value);
    self.showOrigin();}
    ,1500);
}


LliurexMirror.prototype.showOrigin = function showOrigin(){
  this.loadOrigin(this.activedistro);
}

LliurexMirror.prototype.showArchitecture = function showArchitecture(){
  var self = this;
  var credentials=[sessionStorage.username , sessionStorage.password];
  var n4dclass="MirrorManager";
  var n4dmethod="get_mirror_architecture";
  var arglist=[self.activedistro];
  Utils.n4d(credentials, n4dclass, n4dmethod, arglist, function getmirrorarchitecture(response){
    if(response != null && response['status'] == true){
      self.architectures = response['msg'];
      stringarchitectures = "";
      stringarchitectures += self.architectures.indexOf('i386') > -1 ? "32Bits ":"";
      stringarchitectures += self.architectures.indexOf('amd64') > -1 ? "64Bits":"";
      $("#llxmirrorarchitecture").text(stringarchitectures);
    }
  }); 
}

LliurexMirror.prototype.showMirrorSize = function showMirrorSize(){
  var self = this;
  var credentials=[sessionStorage.username , sessionStorage.password];
  var n4dclass="VariablesManager";
  var n4dmethod="get_variable";
  var arglist=['LLIUREXMIRROR'];
  var distro = self.activedistro;
  Utils.n4d(credentials, n4dclass, n4dmethod, arglist, function getvariable(response){
    mirrorinfo = response;
    if ( ! mirrorinfo.hasOwnProperty(self.activedistro)){
      return;
    }
    if ( mirrorinfo[distro].hasOwnProperty('mirror_size')){
      let size = parseFloat(mirrorinfo[distro]['mirror_size']).toPrecision(2);

      $("#llxmirrorsize").text(size + "Gb");
    }
    else{
      $("#llxmirrorsize").text("0 Gb");
    }
  }); 
}

LliurexMirror.prototype.setArchitecture = function setArchitecture(archs){
  var self = this;
  var credentials=[sessionStorage.username , sessionStorage.password];
  var n4dclass="MirrorManager";
  var n4dmethod="set_mirror_architecture";
  var distro = self.activedistro;
  var arglist=[distro,archs];
  Utils.n4d(credentials, n4dclass, n4dmethod, arglist, function(){});
}

LliurexMirror.prototype.setOrig = function setOrig(option,orig){
  var self = this;
  var credentials=[sessionStorage.username , sessionStorage.password];
  var n4dclass="MirrorManager";
  var n4dmethod="set_mirror_orig";
  var distro = self.activedistro;
  var arglist = [distro,orig,option];
  Utils.n4d(credentials, n4dclass, 'set_option_update', [distro,option], function(){
    Utils.n4d(credentials, n4dclass, n4dmethod, arglist, function(){});
  });
}

LliurexMirror.prototype.updateMirror = function updateMirror(){
  var self = this;
  var credentials=[sessionStorage.username , sessionStorage.password];
  var n4dclass="MirrorManager";
  var n4dmethod="update";
  var arglist=['',self.activedistro,{}];
  
  Utils.n4d(credentials, n4dclass, n4dmethod, arglist, function updatemirror(response){
    if(response['status']){
      var updatebutton = document.querySelector('#llxmirrorupdate');
      updatebutton.classList.remove('btn-success');
      updatebutton.classList.add('btn-danger');
      updatebutton.innerHTML = self.translate("lliurex-mirror.Cancel");
      updatebutton.removeEventListener('click',self._updateMirror);
      updatebutton.addEventListener('click',self._stopUpdate,false);
      
      var svg = self.bars[self.activedistro].svg;
      svg.classList.add('lliurexmirrorloader');

      var progresstext = self.bars[self.activedistro].text;
      progresstext.style.color = self.progresscolors['working'];
      if (progresstext.querySelector('.lliurexmirrortextprogress') == null){
        var auxpercentagetext = document.createElement('div');
        auxpercentagetext.classList.add("lliurexmirrortextprogress");
        progresstext.appendChild(auxpercentagetext);
      }
      var percentagetext = progresstext.querySelector('.lliurexmirrortextprogress');

      self.bars[self.activedistro].path.setAttribute('stroke',self.progresscolors['working']);

      self.intervalupdate = setInterval(function(){
        Utils.n4d(credentials,n4dclass,'is_alive',[],function check_alive(response){
          if (response['status']){
            
            Utils.n4d('', n4dclass, 'get_percentage', [response['msg']], function getpercentage(response){
              percentagetext.innerHTML = response['msg'].toString() + "%";
              if (response['msg'] < 1){
                response['msg'] = 1;
              }
              self.progress = (100 - response['msg']) / 100;
              self.bars[self.activedistro].animate(1 - self.progress );
            });
          }
          else{
            Utils.n4d(credentials,'VariablesManager','get_variable',['LLIUREXMIRROR'],function get_mirror_info(response){

              var infomirror = response[self.activedistro];
              var status = infomirror['status_mirror'];

              if(status == 'Ok'){
                self.bars[self.activedistro].path.setAttribute('stroke',self.progresscolors['ok']);
                progresstext.style.color = self.progresscolors['ok'];
                Utils.msg(self.translate("Mirror finished with success"),"");
              }
              else{
               self.bars[self.activedistro].path.setAttribute('stroke',self.progresscolors['error']); 
               progresstext.style.color = self.progresscolors['error'];
               Utils.msg(self.translate("Mirror finished with error")+infomirror['exception_msg'],"");
              }
              percentagetext.remove();
              updatebutton.classList.add('btn-success');
              updatebutton.classList.remove('btn-danger');
              updatebutton.innerHTML = self.translate("lliurex-mirror.Update");
              svg.classList.remove('lliurexmirrorloader');
              clearInterval(self.intervalupdate);
              self.checkLliurexUpdate();
              });            
            }
       });
      }
      ,5000);
    }
  });
}


LliurexMirror.prototype.stopUpdate = function stopUpdate(){
  var self = this;
  var credentials=[sessionStorage.username , sessionStorage.password];
  var n4dclass="MirrorManager";
  var n4dmethod="stopupdate";
  var buttonupdate = document.querySelector('#llxmirrorupdate');
  buttonupdate.removeEventListener('click',self._stopUpdate,false);
  buttonupdate.innerHTML = "Waiting...";
  buttonupdate.classList.remove('btn-danger');
  var arglist=[];
  Utils.n4d(credentials, n4dclass, n4dmethod, arglist, function stopupdate(response){
    buttonupdate.addEventListener('click',self._updateMirror);
  });
}

LliurexMirror.prototype.checkLliurexUpdate = function checkLliurexUpdate(){
  var self = this;
  var credentials=[sessionStorage.username , sessionStorage.password];
  var n4dclass="MirrorManager";
  var n4dmethod="is_update_available";
  var arglist=[self.activedistro];
  var mirrorupdatemessage=document.querySelector('#llxmirrorupdatepanel');
  Utils.n4d(credentials, n4dclass, n4dmethod, arglist, function ismirrorupdate(response){
    if(response == null || response['action']!='update'){   
       $('#llxmirrorupdatepanel').text('')
    }
    else{
      var messagecontainer = document.createElement('div');
      var button = document.createElement('button');
      var tempdiv = document.createElement('div');
      var message = document.createElement('strong');
      var z = document.querySelector("#llxmirrorupdatepanel");
      
      messagecontainer.classList.add('alert','alert-dismissible','alert-danger');
      button.type = "button";
      button.classList = ["close"];
      button.innerHTML = "x";
      button.setAttribute("data-dismiss","alert");
      message.innerHTML = self.translate("lliurex-mirror.message");
      
      messagecontainer.appendChild(button);
      messagecontainer.appendChild(message);
      z.appendChild(messagecontainer);
     
    }
  }); 
}


var llxmirror = new LliurexMirror();
llxmirror.bindEvents();

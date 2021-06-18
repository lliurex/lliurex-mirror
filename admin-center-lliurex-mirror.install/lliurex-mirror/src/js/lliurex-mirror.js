function LliurexMirror(){
  this.distros = {'llx16':{}, 'llx19':{}, 'llx21':{}};
  this.activedistro = 'llx21';
  this.progresscolors = {'new':'#4caf50' ,'ok' : '#4caf50' , 'error' : 'red', 'working':'#03A9F4','default':'black'};
  this.bars = {};
  this.edit = null;
  this.progressoptionsdefault = {color:this.progresscolors['ok'], trailcolor:'#9f9f9f', trailWidth:3, strokeWidth: 3, easing: 'easeInOut', text: {value:''},duration:10000};
  this.intervalupdate = null;
  this.progress = 0;
  this.credentials = [sessionStorage.username , sessionStorage.password];
  this.n4dclass = "MirrorManager";
}

LliurexMirror.prototype.translate = function translate(text){
  return (i18n.gettext("lliurex-mirror", text));
}


LliurexMirror.prototype.loadMirrorInfo = function loadMirrorInfo(info){
  let self = this;
  let availabledistros = Object.keys(this.distros);
  availabledistros.forEach(function load(distro){
    $.extend(self.distros[distro],self.distros[distro],info[distro]);
  });
}

LliurexMirror.prototype.loadProgressBar = function loadProgressBar(container,distro) {
  let self = this;
  let progressoptions = self.progressoptionsdefault;
  let status_mirror = self.distros[distro]['status_mirror'].toLowerCase();
  progressoptions['color'] = self.progresscolors.hasOwnProperty(status_mirror) ? self.progresscolors[status_mirror] : self.progresscolors['default'];  
  progressoptions['text']['value'] = distro;
  self.bars[distro] = new ProgressBar.Circle(container, progressoptions);
  self.bars[distro].animate(1 - (100 - self.distros[distro]['progress']) / 100 );
}

LliurexMirror.prototype.loadOrigin = function loadOrigin(distro){
  let self = this;
  Utils.n4d(self.credentials, self.n4dclass, "get_option_update", [distro], function getoptionupdate(response){
    if(response != null && $.isNumeric(response)){
      Utils.n4d(self.credentials, self.n4dclass, "get_mirror_orig", [distro,response], function getmirrororig(response){
        if(response != null && response != ""){
          self.distros[distro]['orig'] = response;
          self.showOrig(response);
        }
      });
    }
  });
}

LliurexMirror.prototype.showOrig = function showOrig(text){
  $("#llxmirrororig").text(text);
}

LliurexMirror.prototype.bindEvents = function bindEvents(){
  let self = this;
  let distro = self.activedistro;
  console.log('Binding events')
  $(document).on("moduleLoaded",function(e,args){
  	if (args['moduleName'] != "lliurex-mirror"){
  		return ;
    }
    Utils.n4d('', '', 'get_variable', ['LLIUREXMIRROR'], function get_variables(response){
      console.log('Getting mirror variables from server')
      self.loadMirrorInfo(response);
      self.loadProgressBar('#llxmirrorprogress',distro);
      self.loadOrigin(distro);
      self.showArchitecture();
      //self.showMirrorSize();
      self.checkLliurexUpdate();
    });
  });
  $("#llxmirrormenuarch").on('click',function modifyarch(e,args){
    console.log('Changing architecture')
    self.showOptionsMenu(self,'#llxmirrormenuarch',self.buildArchMenuConfig);
  });

  $("#llxmirrormenuorig").on('click',function modifyarch(e,args){
    console.log('Changing architecture')
    self.showOptionsMenu(self,'#llxmirrormenuorig',self.buildOrigMenuConfig);
  });

  let buttonupdate = document.querySelector("#llxmirrorupdate");
  self._updateMirror = self.updateMirror.bind(self);
  self._stopUpdate = self.stopUpdate.bind(self);
  buttonupdate.addEventListener('click',self._updateMirror,false);
};

LliurexMirror.prototype.showOptionsMenu = function showOptionsMenu(self,menuid,buildfunction){
  let configuration = document.querySelectorAll('#llxmirrorconfiguration')[0];
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
  let self = this;
  let buttonGroups = document.createElement('div');
  let enablei386 = document.createElement('a');
  let enableamd64 = document.createElement('a');
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
    let archs = [];
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
  let container = document.querySelector(idcontainer);
  let fc = container.firstChild;
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
  let self = this;
  let buttonGroups = document.createElement('div');
  buttonGroups.classList = ["btn-group"];
  buttonGroups.classList.add("btn-group-justified");
  buttonGroups.classList.add("btn-group-raised");
  let internet = document.createElement('a');
  let url = document.createElement('a');
  internet.classList.add('btn');
  url.classList.add('btn');
  internet.classList.add('btn-raised');
  url.classList.add('btn-raised');
  internet.innerHTML = "LliureX.net";
  url.innerHTML = "Custom url";

  buttonGroups.appendChild(internet);
  buttonGroups.appendChild(url);
  

  let customurlform = document.createElement('div');
  customurlform.classList.add('form-group');
  customurlform.classList.add('label-floating');
  customurlform.classList.add('llxmirrorhidden');
  let labelcustomurl = document.createElement('label');
  labelcustomurl.classList.add('control-label');
  labelcustomurl.setAttribute('for','customurl');
  labelcustomurl.innerHTML = 'Write mirror url without http://';
  let inputcustomurl = document.createElement('input');
  let distro = self.activedistro;
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
    let credentials=[sessionStorage.username , sessionStorage.password];
    let n4dclass="MirrorManager";
    let n4dmethod="get_mirror_orig";
    let arglist=[self.activedistro,response];
    console.log('Getting optionupdate from server')
    Utils.n4d(credentials, n4dclass, n4dmethod, arglist, function getmirrororig(response){
      let value = response;
      if (value.toLowerCase() == 'lliurex.net/focal'){
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

  let container = document.querySelector(idcontainer);
  let fc = container.firstChild;
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
  let self = this;
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
  let self = this;
  let credentials=[sessionStorage.username , sessionStorage.password];
  let n4dclass="MirrorManager";
  let n4dmethod="get_mirror_architecture";
  let arglist=[self.activedistro];
  Utils.n4d(credentials, n4dclass, n4dmethod, arglist, function getmirrorarchitecture(response){
    if(response != null && Array.isArray(response)){
      self.architectures = response;
      stringarchitectures = "";
      stringarchitectures += self.architectures.indexOf('i386') > -1 ? "32Bits ":"";
      stringarchitectures += self.architectures.indexOf('amd64') > -1 ? "64Bits":"";
      $("#llxmirrorarchitecture").text(stringarchitectures);
    }
  }); 
}

LliurexMirror.prototype.showMirrorSize = function showMirrorSize(){
  let self = this;
  let credentials = null;
  let n4dclass="";
  let n4dmethod="get_variable";
  let arglist=['LLIUREXMIRROR'];
  let distro = self.activedistro;
  console.log('Getting mirror variable from server')
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
  let self = this;
  let credentials=[sessionStorage.username , sessionStorage.password];
  let n4dclass="MirrorManager";
  let n4dmethod="set_mirror_architecture";
  let distro = self.activedistro;
  let arglist=[distro,archs];
  console.log('Setting architecture')
  Utils.n4d(credentials, n4dclass, n4dmethod, arglist, function(){});
}

LliurexMirror.prototype.setOrig = function setOrig(option,orig){
  let self = this;
  let credentials=[sessionStorage.username , sessionStorage.password];
  let n4dclass="MirrorManager";
  let n4dmethod="set_mirror_orig";
  let distro = self.activedistro;
  let arglist = [distro,orig,option];
  console.log('Setting orig')
  Utils.n4d(credentials, n4dclass, 'set_option_update', [distro,option], function(){
    Utils.n4d(credentials, n4dclass, n4dmethod, arglist, function(){});
  });
}

LliurexMirror.prototype.updateMirror = function updateMirror(){
  let self = this;
  let credentials=[sessionStorage.username , sessionStorage.password];
  let n4dclass="MirrorManager";
  let n4dmethod="update";
  let arglist=['','',self.activedistro,'{}'];
  console.log('Updating mirror')
  Utils.n4d(credentials, n4dclass, n4dmethod, arglist, function updatemirror(response){
    if(response){
      let updatebutton = document.querySelector('#llxmirrorupdate');
      updatebutton.classList.remove('btn-success');
      updatebutton.classList.add('btn-danger');
      updatebutton.innerHTML = self.translate("lliurex-mirror.Cancel");
      console.log('Changing button triggers to stop method')
      updatebutton.removeEventListener('click',self._updateMirror);
      updatebutton.addEventListener('click',self._stopUpdate,false);
      
      let svg = self.bars[self.activedistro].svg;
      // DISABLED (CPU EATER)
      // svg.classList.add('lliurexmirrorloader');

      let progresstext = self.bars[self.activedistro].text;
      progresstext.style.color = self.progresscolors['working'];
      if (progresstext.querySelector('.lliurexmirrortextprogress') == null){
        let auxpercentagetext = document.createElement('div');
        auxpercentagetext.classList.add("lliurexmirrortextprogress");
        progresstext.appendChild(auxpercentagetext);
      }
      let percentagetext = progresstext.querySelector('.lliurexmirrortextprogress');

      self.bars[self.activedistro].path.setAttribute('stroke',self.progresscolors['working']);

      self.intervalupdate = setInterval(function(){
        console.log('Checking alive with interval 15s')
        Utils.n4d(credentials,n4dclass,'is_alive',[],function check_alive(response){
          console.log('is alive? '+response['status'])
          if (response['status']){
            console.log('Checking percentage')
            Utils.n4d(credentials, n4dclass, 'get_percentage', [response['msg']], function getpercentage(response){
              console.log('get_percentage'+(response))
              //debugger
              if ($.isNumeric(response)){
                percentagetext.innerHTML = response + "%";
                if (response < 1){
                  response = 1;
                }
                self.progress = (100 - response) / 100;
                self.bars[self.activedistro].animate(1 - self.progress );
              }else{
                console.log('Warning! response from get_percentage is not a number')
              }
            });
          }
          else{
            console.log('No status in response is_alive, getting mirror server vars')
            Utils.n4d('','','get_variable',['LLIUREXMIRROR'],function get_mirror_info(response){
              let infomirror = response[self.activedistro];
              let status = infomirror['status_mirror'];

              if(status == 'Ok'){
                self.bars[self.activedistro].path.setAttribute('stroke',self.progresscolors['ok']);
                progresstext.style.color = self.progresscolors['ok'];
                Utils.msg(self.translate("Mirror finished with success"),"");
                console.log('Mirror finished successfuly')
              }
              else{
               self.bars[self.activedistro].path.setAttribute('stroke',self.progresscolors['error']); 
               progresstext.style.color = self.progresscolors['error'];
               Utils.msg(self.translate("Mirror finished with error")+infomirror['exception_msg'],"");
               console.log('Mirror finished with error '+infomirror['exception_msg'])
              }
              percentagetext.remove();
              console.log('Changing button to success')
              updatebutton.classList.add('btn-success');
              updatebutton.classList.remove('btn-danger');
              updatebutton.innerHTML = self.translate("lliurex-mirror.Update");
              svg.classList.remove('lliurexmirrorloader');
              console.log('Clearing last interval')
              clearInterval(self.intervalupdate);
              console.log('Calling checkLliurexPpdate')
              self.checkLliurexUpdate();
              });            
            }
       });
      }
      ,15000);
    }
  });
}


LliurexMirror.prototype.stopUpdate = function stopUpdate(){
  let self = this;
  let credentials=[sessionStorage.username , sessionStorage.password];
  let n4dclass="MirrorManager";
  let n4dmethod="stopupdate";
  let buttonupdate = document.querySelector('#llxmirrorupdate');
  console.log('Calling stopupdate')
  buttonupdate.removeEventListener('click',self._stopUpdate,false);
  buttonupdate.innerHTML = "Waiting...";
  buttonupdate.classList.remove('btn-danger');
  let arglist=[];
  Utils.n4d(credentials, n4dclass, n4dmethod, arglist, function stopupdate(response){
    console.log('StopUpdate ended, changing button to allow update again')
    buttonupdate.addEventListener('click',self._updateMirror);
  });
}

LliurexMirror.prototype.checkLliurexUpdate = function checkLliurexUpdate(){
  let self = this;
  let credentials=[sessionStorage.username , sessionStorage.password];
  let n4dclass="MirrorManager";
  let n4dmethod="is_update_available";
  let arglist=[self.activedistro];
  let mirrorupdatemessage=document.querySelector('#llxmirrorupdatepanel');
  console.log('Called checkLliurexUpdate (is_update_available)')
  Utils.n4d(credentials, n4dclass, n4dmethod, arglist, function ismirrorupdate(response){
    if(response == null || response['action']!='update'){   
      console.log('Update not available')
       $('#llxmirrorupdatepanel').text('')
    }
    else{
      console.log('Update available')
      let messagecontainer = document.createElement('div');
      let button = document.createElement('button');
      let tempdiv = document.createElement('div');
      let message = document.createElement('strong');
      let z = document.querySelector("#llxmirrorupdatepanel");
      
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


let llxmirror = new LliurexMirror();
llxmirror.bindEvents();

"use strict";(self.webpackChunkknx_frontend=self.webpackChunkknx_frontend||[]).push([["9469"],{42256:function(e,t,s){s.d(t,{I:function(){return n}});var a=s(44734),i=s(56038),r=(s(16280),s(25276),s(44114),s(54554),s(18111),s(7588),s(33110),s(26099),s(58335),s(23500),function(){return(0,i.A)((function e(){var t=arguments.length>0&&void 0!==arguments[0]?arguments[0]:window.localStorage;(0,a.A)(this,e),this._storage={},this._listeners={},this.storage=t,this.storage===window.localStorage&&window.addEventListener("storage",(e=>{e.key&&this.hasKey(e.key)&&(this._storage[e.key]=e.newValue?JSON.parse(e.newValue):e.newValue,this._listeners[e.key]&&this._listeners[e.key].forEach((t=>t(e.oldValue?JSON.parse(e.oldValue):e.oldValue,this._storage[e.key]))))}))}),[{key:"addFromStorage",value:function(e){if(!this._storage[e]){var t=this.storage.getItem(e);t&&(this._storage[e]=JSON.parse(t))}}},{key:"subscribeChanges",value:function(e,t){return this._listeners[e]?this._listeners[e].push(t):this._listeners[e]=[t],()=>{this.unsubscribeChanges(e,t)}}},{key:"unsubscribeChanges",value:function(e,t){if(e in this._listeners){var s=this._listeners[e].indexOf(t);-1!==s&&this._listeners[e].splice(s,1)}}},{key:"hasKey",value:function(e){return e in this._storage}},{key:"getValue",value:function(e){return this._storage[e]}},{key:"setValue",value:function(e,t){var s=this._storage[e];this._storage[e]=t;try{void 0===t?this.storage.removeItem(e):this.storage.setItem(e,JSON.stringify(t))}catch(a){}finally{this._listeners[e]&&this._listeners[e].forEach((e=>e(s,t)))}}}])}()),o={};function n(e){return(t,s)=>{if("object"==typeof s)throw new Error("This decorator does not support this compilation type.");var a,i=e.storage||"localStorage";i&&i in o?a=o[i]:(a=new r(window[i]),o[i]=a);var n=e.key||String(s);a.addFromStorage(n);var l=!1!==e.subscribe?e=>a.subscribeChanges(n,((t,a)=>{e.requestUpdate(s,t)})):void 0,u=()=>a.hasKey(n)?e.deserializer?e.deserializer(a.getValue(n)):a.getValue(n):void 0,h=(t,i)=>{var r;e.state&&(r=u()),a.setValue(n,e.serializer?e.serializer(i):i),e.state&&t.requestUpdate(s,r)},c=t.performUpdate;if(t.performUpdate=function(){this.__initialized=!0,c.call(this)},e.subscribe){var d=t.connectedCallback,g=t.disconnectedCallback;t.connectedCallback=function(){d.call(this);this.__unbsubLocalStorage||(this.__unbsubLocalStorage=null==l?void 0:l(this))},t.disconnectedCallback=function(){var e;g.call(this);var t=this;null===(e=t.__unbsubLocalStorage)||void 0===e||e.call(t),t.__unbsubLocalStorage=void 0}}var p,_=Object.getOwnPropertyDescriptor(t,s);if(void 0===_)p={get(){return u()},set(e){(this.__initialized||void 0===u())&&h(this,e)},configurable:!0,enumerable:!0};else{var v=_.set;p=Object.assign(Object.assign({},_),{},{get(){return u()},set(e){(this.__initialized||void 0===u())&&h(this,e),null==v||v.call(this,e)}})}Object.defineProperty(t,s,p)}}},92821:function(e,t,s){s.a(e,(async function(e,t){try{var a=s(44734),i=s(56038),r=s(69683),o=s(6454),n=(s(28706),s(62826)),l=s(96196),u=s(77845),h=s(94333),c=s(89473),d=s(89600),g=(s(60961),e([c,d]));[c,d]=g.then?(await g)():g;var p,_,v,y,b,f,m=e=>e,k=function(e){function t(){var e;(0,a.A)(this,t);for(var s=arguments.length,i=new Array(s),o=0;o<s;o++)i[o]=arguments[o];return(e=(0,r.A)(this,t,[].concat(i))).disabled=!1,e.progress=!1,e.appearance="accent",e.variant="brand",e}return(0,o.A)(t,e),(0,i.A)(t,[{key:"render",value:function(){var e=this.progress||this._result?"accent":this.appearance;return(0,l.qy)(p||(p=m`
      <ha-button
        .appearance=${0}
        .disabled=${0}
        .loading=${0}
        .variant=${0}
        class=${0}
      >
        ${0}

        <slot>${0}</slot>
      </ha-button>
      ${0}
    `),e,this.disabled,this.progress,"success"===this._result?"success":"error"===this._result?"danger":this.variant,(0,h.H)({result:!!this._result,success:"success"===this._result,error:"error"===this._result}),this.iconPath?(0,l.qy)(_||(_=m`<ha-svg-icon
              .path=${0}
              slot="start"
            ></ha-svg-icon>`),this.iconPath):l.s6,this.label,this._result?(0,l.qy)(v||(v=m`
            <div class="progress">
              ${0}
            </div>
          `),"success"===this._result?(0,l.qy)(y||(y=m`<ha-svg-icon .path=${0}></ha-svg-icon>`),"M9,20.42L2.79,14.21L5.62,11.38L9,14.77L18.88,4.88L21.71,7.71L9,20.42Z"):"error"===this._result?(0,l.qy)(b||(b=m`<ha-svg-icon .path=${0}></ha-svg-icon>`),"M2.2,16.06L3.88,12L2.2,7.94L6.26,6.26L7.94,2.2L12,3.88L16.06,2.2L17.74,6.26L21.8,7.94L20.12,12L21.8,16.06L17.74,17.74L16.06,21.8L12,20.12L7.94,21.8L6.26,17.74L2.2,16.06M13,17V15H11V17H13M13,13V7H11V13H13Z"):l.s6):l.s6)}},{key:"actionSuccess",value:function(){this._setResult("success")}},{key:"actionError",value:function(){this._setResult("error")}},{key:"_setResult",value:function(e){this._result=e,setTimeout((()=>{this._result=void 0}),2e3)}}])}(l.WF);k.styles=(0,l.AH)(f||(f=m`
    :host {
      outline: none;
      display: inline-block;
      position: relative;
    }

    :host([progress]) {
      pointer-events: none;
    }

    .progress {
      bottom: 0;
      display: flex;
      justify-content: center;
      align-items: center;
      position: absolute;
      top: 0;
      width: 100%;
    }

    ha-button {
      width: 100%;
    }

    ha-button.result::part(start),
    ha-button.result::part(end),
    ha-button.result::part(label),
    ha-button.result::part(caret),
    ha-button.result::part(spinner) {
      visibility: hidden;
    }

    ha-svg-icon {
      color: var(--white-color);
    }
  `)),(0,n.__decorate)([(0,u.MZ)()],k.prototype,"label",void 0),(0,n.__decorate)([(0,u.MZ)({type:Boolean})],k.prototype,"disabled",void 0),(0,n.__decorate)([(0,u.MZ)({type:Boolean,reflect:!0})],k.prototype,"progress",void 0),(0,n.__decorate)([(0,u.MZ)()],k.prototype,"appearance",void 0),(0,n.__decorate)([(0,u.MZ)({attribute:!1})],k.prototype,"iconPath",void 0),(0,n.__decorate)([(0,u.MZ)()],k.prototype,"variant",void 0),(0,n.__decorate)([(0,u.wk)()],k.prototype,"_result",void 0),k=(0,n.__decorate)([(0,u.EM)("ha-progress-button")],k),t()}catch(w){t(w)}}))},94764:function(e,t,s){s.a(e,(async function(e,a){try{s.r(t),s.d(t,{TTSTryDialog:function(){return $}});var i=s(61397),r=s(50264),o=s(44734),n=s(56038),l=s(69683),u=s(6454),h=(s(28706),s(62826)),c=s(96196),d=s(77845),g=s(42256),p=s(92542),_=s(92821),v=s(95637),y=(s(67591),s(62146)),b=s(39396),f=s(10234),m=e([_]);_=(m.then?(await m)():m)[0];var k,w,L=e=>e,$=function(e){function t(){var e;(0,o.A)(this,t);for(var s=arguments.length,a=new Array(s),i=0;i<s;i++)a[i]=arguments[i];return(e=(0,l.A)(this,t,[].concat(a)))._loadingExample=!1,e._valid=!1,e}return(0,u.A)(t,e),(0,n.A)(t,[{key:"showDialog",value:function(e){this._params=e,this._valid=Boolean(this._defaultMessage)}},{key:"closeDialog",value:function(){this._params=void 0,(0,p.r)(this,"dialog-closed",{dialog:this.localName})}},{key:"_defaultMessage",get:function(){var e,t,s=null===(e=this._params.language)||void 0===e?void 0:e.substring(0,2),a=this.hass.locale.language.substring(0,2);return s&&null!==(t=this._messages)&&void 0!==t&&t[s]?this._messages[s]:s===a?this.hass.localize("ui.dialogs.tts-try.message_example"):""}},{key:"render",value:function(){return this._params?(0,c.qy)(k||(k=L`
      <ha-dialog
        open
        @closed=${0}
        .heading=${0}
      >
        <ha-textarea
          autogrow
          id="message"
          .label=${0}
          .placeholder=${0}
          .value=${0}
          @input=${0}
          ?dialogInitialFocus=${0}
        >
        </ha-textarea>

        <ha-progress-button
          .progress=${0}
          ?dialogInitialFocus=${0}
          slot="primaryAction"
          @click=${0}
          .disabled=${0}
          .iconPath=${0}
        >
          ${0}
        </ha-progress-button>
      </ha-dialog>
    `),this.closeDialog,(0,v.l)(this.hass,this.hass.localize("ui.dialogs.tts-try.header")),this.hass.localize("ui.dialogs.tts-try.message"),this.hass.localize("ui.dialogs.tts-try.message_placeholder"),this._defaultMessage,this._inputChanged,!this._defaultMessage,this._loadingExample,Boolean(this._defaultMessage),this._playExample,!this._valid,"M12,20C7.59,20 4,16.41 4,12C4,7.59 7.59,4 12,4C16.41,4 20,7.59 20,12C20,16.41 16.41,20 12,20M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M10,16.5L16,12L10,7.5V16.5Z",this.hass.localize("ui.dialogs.tts-try.play")):c.s6}},{key:"_inputChanged",value:(a=(0,r.A)((0,i.A)().m((function e(){var t;return(0,i.A)().w((function(e){for(;;)switch(e.n){case 0:this._valid=Boolean(null===(t=this._messageInput)||void 0===t?void 0:t.value);case 1:return e.a(2)}}),e,this)}))),function(){return a.apply(this,arguments)})},{key:"_playExample",value:(s=(0,r.A)((0,i.A)().m((function e(){var t,s,a,r,o,n,l,u,h;return(0,i.A)().w((function(e){for(;;)switch(e.p=e.n){case 0:if(s=null===(t=this._messageInput)||void 0===t?void 0:t.value){e.n=1;break}return e.a(2);case 1:return a=this._params.engine,r=this._params.language,o=this._params.voice,r&&(this._messages=Object.assign(Object.assign({},this._messages),{},{[r.substring(0,2)]:s})),this._loadingExample=!0,(n=new Audio).play(),e.p=2,e.n=3,(0,y.S_)(this.hass,{platform:a,message:s,language:r,options:{voice:o}});case 3:u=e.v,l=u.path,e.n=5;break;case 4:return e.p=4,h=e.v,this._loadingExample=!1,(0,f.K$)(this,{text:`Unable to load example. ${h.error||h.body||h}`,warning:!0}),e.a(2);case 5:n.src=l,n.addEventListener("canplaythrough",(()=>n.play())),n.addEventListener("playing",(()=>{this._loadingExample=!1})),n.addEventListener("error",(()=>{(0,f.K$)(this,{title:"Error playing audio."}),this._loadingExample=!1}));case 6:return e.a(2)}}),e,this,[[2,4]])}))),function(){return s.apply(this,arguments)})}]);var s,a}(c.WF);$.styles=[b.nA,(0,c.AH)(w||(w=L`
      ha-dialog {
        --mdc-dialog-max-width: 500px;
      }
      ha-textarea,
      ha-select {
        width: 100%;
      }
      ha-select {
        margin-top: 8px;
      }
      .loading {
        height: 36px;
      }
    `))],(0,h.__decorate)([(0,d.MZ)({attribute:!1})],$.prototype,"hass",void 0),(0,h.__decorate)([(0,d.wk)()],$.prototype,"_loadingExample",void 0),(0,h.__decorate)([(0,d.wk)()],$.prototype,"_params",void 0),(0,h.__decorate)([(0,d.wk)()],$.prototype,"_valid",void 0),(0,h.__decorate)([(0,d.P)("#message")],$.prototype,"_messageInput",void 0),(0,h.__decorate)([(0,g.I)({key:"ttsTryMessages",state:!1,subscribe:!1})],$.prototype,"_messages",void 0),$=(0,h.__decorate)([(0,d.EM)("dialog-tts-try")],$),a()}catch(A){a(A)}}))}}]);
//# sourceMappingURL=9469.0d8aae460a45a63f.js.map
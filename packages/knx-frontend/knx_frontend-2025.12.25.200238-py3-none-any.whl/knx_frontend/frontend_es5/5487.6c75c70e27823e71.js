"use strict";(self.webpackChunkknx_frontend=self.webpackChunkknx_frontend||[]).push([["5487"],{34818:function(e,t,i){i.r(t),i.d(t,{HaTTSSelector:function(){return W}});var n,a,r,s,o=i(44734),l=i(56038),u=i(69683),d=i(6454),h=(i(28706),i(62826)),c=i(96196),v=i(77845),p=i(61397),_=i(50264),g=i(31432),f=i(25460),y=(i(50113),i(74423),i(62062),i(18111),i(20116),i(61701),i(26099),i(16034),i(92542)),b=i(55124),k=i(91889),$=i(40404),A=i(62146),M=(i(56565),i(69869),i(41144)),q=e=>e,Z="__NONE_OPTION__",m=function(e){function t(){var e;(0,o.A)(this,t);for(var i=arguments.length,n=new Array(i),a=0;a<i;a++)n[a]=arguments[a];return(e=(0,u.A)(this,t,[].concat(n))).disabled=!1,e.required=!1,e._debouncedUpdateEngines=(0,$.s)((()=>e._updateEngines()),500),e}return(0,d.A)(t,e),(0,l.A)(t,[{key:"render",value:function(){if(!this._engines)return c.s6;var e=this.value;if(!e&&this.required){for(var t=0,i=Object.values(this.hass.entities);t<i.length;t++){var s=i[t];if("cloud"===s.platform&&"tts"===(0,M.m)(s.entity_id)){e=s.entity_id;break}}if(!e){var o,l=(0,g.A)(this._engines);try{for(l.s();!(o=l.n()).done;){var u,d=o.value;if(0!==(null==d||null===(u=d.supported_languages)||void 0===u?void 0:u.length)){e=d.engine_id;break}}}catch(h){l.e(h)}finally{l.f()}}}return e||(e=Z),(0,c.qy)(n||(n=q`
      <ha-select
        .label=${0}
        .value=${0}
        .required=${0}
        .disabled=${0}
        @selected=${0}
        @closed=${0}
        fixedMenuPosition
        naturalMenuWidth
      >
        ${0}
        ${0}
      </ha-select>
    `),this.label||this.hass.localize("ui.components.tts-picker.tts"),e,this.required,this.disabled,this._changed,b.d,this.required?c.s6:(0,c.qy)(a||(a=q`<ha-list-item .value=${0}>
              ${0}
            </ha-list-item>`),Z,this.hass.localize("ui.components.tts-picker.none")),this._engines.map((t=>{var i,n;if(t.deprecated&&t.engine_id!==e)return c.s6;if(t.engine_id.includes(".")){var a=this.hass.states[t.engine_id];n=a?(0,k.u)(a):t.engine_id}else n=t.name||t.engine_id;return(0,c.qy)(r||(r=q`<ha-list-item
            .value=${0}
            .disabled=${0}
          >
            ${0}
          </ha-list-item>`),t.engine_id,0===(null===(i=t.supported_languages)||void 0===i?void 0:i.length),n)})))}},{key:"willUpdate",value:function(e){(0,f.A)(t,"willUpdate",this,3)([e]),this.hasUpdated?e.has("language")&&this._debouncedUpdateEngines():this._updateEngines()}},{key:"_updateEngines",value:(i=(0,_.A)((0,p.A)().m((function e(){var t,i;return(0,p.A)().w((function(e){for(;;)switch(e.n){case 0:return e.n=1,(0,A.Xv)(this.hass,this.language,this.hass.config.country||void 0);case 1:if(this._engines=e.v.providers,this.value){e.n=2;break}return e.a(2);case 2:i=this._engines.find((e=>e.engine_id===this.value)),(0,y.r)(this,"supported-languages-changed",{value:null==i?void 0:i.supported_languages}),i&&0!==(null===(t=i.supported_languages)||void 0===t?void 0:t.length)||(this.value=void 0,(0,y.r)(this,"value-changed",{value:this.value}));case 3:return e.a(2)}}),e,this)}))),function(){return i.apply(this,arguments)})},{key:"_changed",value:function(e){var t,i=e.target;!this.hass||""===i.value||i.value===this.value||void 0===this.value&&i.value===Z||(this.value=i.value===Z?void 0:i.value,(0,y.r)(this,"value-changed",{value:this.value}),(0,y.r)(this,"supported-languages-changed",{value:null===(t=this._engines.find((e=>e.engine_id===this.value)))||void 0===t?void 0:t.supported_languages}))}}]);var i}(c.WF);m.styles=(0,c.AH)(s||(s=q`
    ha-select {
      width: 100%;
    }
  `)),(0,h.__decorate)([(0,v.MZ)()],m.prototype,"value",void 0),(0,h.__decorate)([(0,v.MZ)()],m.prototype,"label",void 0),(0,h.__decorate)([(0,v.MZ)()],m.prototype,"language",void 0),(0,h.__decorate)([(0,v.MZ)({attribute:!1})],m.prototype,"hass",void 0),(0,h.__decorate)([(0,v.MZ)({type:Boolean,reflect:!0})],m.prototype,"disabled",void 0),(0,h.__decorate)([(0,v.MZ)({type:Boolean})],m.prototype,"required",void 0),(0,h.__decorate)([(0,v.wk)()],m.prototype,"_engines",void 0),m=(0,h.__decorate)([(0,v.EM)("ha-tts-picker")],m);var w,E,S=e=>e,W=function(e){function t(){var e;(0,o.A)(this,t);for(var i=arguments.length,n=new Array(i),a=0;a<i;a++)n[a]=arguments[a];return(e=(0,u.A)(this,t,[].concat(n))).disabled=!1,e.required=!0,e}return(0,d.A)(t,e),(0,l.A)(t,[{key:"render",value:function(){var e,t;return(0,c.qy)(w||(w=S`<ha-tts-picker
      .hass=${0}
      .value=${0}
      .label=${0}
      .helper=${0}
      .language=${0}
      .disabled=${0}
      .required=${0}
    ></ha-tts-picker>`),this.hass,this.value,this.label,this.helper,(null===(e=this.selector.tts)||void 0===e?void 0:e.language)||(null===(t=this.context)||void 0===t?void 0:t.language),this.disabled,this.required)}}])}(c.WF);W.styles=(0,c.AH)(E||(E=S`
    ha-tts-picker {
      width: 100%;
    }
  `)),(0,h.__decorate)([(0,v.MZ)({attribute:!1})],W.prototype,"hass",void 0),(0,h.__decorate)([(0,v.MZ)({attribute:!1})],W.prototype,"selector",void 0),(0,h.__decorate)([(0,v.MZ)()],W.prototype,"value",void 0),(0,h.__decorate)([(0,v.MZ)()],W.prototype,"label",void 0),(0,h.__decorate)([(0,v.MZ)()],W.prototype,"helper",void 0),(0,h.__decorate)([(0,v.MZ)({type:Boolean})],W.prototype,"disabled",void 0),(0,h.__decorate)([(0,v.MZ)({type:Boolean})],W.prototype,"required",void 0),(0,h.__decorate)([(0,v.MZ)({attribute:!1})],W.prototype,"context",void 0),W=(0,h.__decorate)([(0,v.EM)("ha-selector-tts")],W)},62146:function(e,t,i){i.d(t,{EF:function(){return s},S_:function(){return n},Xv:function(){return o},ni:function(){return r},u1:function(){return l},z3:function(){return u}});var n=(e,t)=>e.callApi("POST","tts_get_url",t),a="media-source://tts/",r=e=>e.startsWith(a),s=e=>e.substring(19),o=(e,t,i)=>e.callWS({type:"tts/engine/list",language:t,country:i}),l=(e,t)=>e.callWS({type:"tts/engine/get",engine_id:t}),u=(e,t,i)=>e.callWS({type:"tts/engine/voices",engine_id:t,language:i})}}]);
//# sourceMappingURL=5487.6c75c70e27823e71.js.map
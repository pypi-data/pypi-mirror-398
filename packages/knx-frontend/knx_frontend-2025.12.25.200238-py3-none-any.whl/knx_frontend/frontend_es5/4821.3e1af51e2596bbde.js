"use strict";(self.webpackChunkknx_frontend=self.webpackChunkknx_frontend||[]).push([["4821"],{97956:function(e,t,i){i.r(t),i.d(t,{HaSTTSelector:function(){return T}});var a,n,s,r,o=i(44734),l=i(56038),d=i(69683),u=i(6454),h=(i(28706),i(62826)),v=i(96196),c=i(77845),p=i(61397),_=i(50264),g=i(31432),f=i(25460),y=(i(50113),i(74423),i(62062),i(18111),i(20116),i(61701),i(26099),i(16034),i(92542)),b=i(55124),k=i(91889),$=i(40404),M=i(61970),A=(i(56565),i(69869),i(41144)),q=e=>e,Z="__NONE_OPTION__",m=function(e){function t(){var e;(0,o.A)(this,t);for(var i=arguments.length,a=new Array(i),n=0;n<i;n++)a[n]=arguments[n];return(e=(0,d.A)(this,t,[].concat(a))).disabled=!1,e.required=!1,e._debouncedUpdateEngines=(0,$.s)((()=>e._updateEngines()),500),e}return(0,u.A)(t,e),(0,l.A)(t,[{key:"render",value:function(){if(!this._engines)return v.s6;var e=this.value;if(!e&&this.required){for(var t=0,i=Object.values(this.hass.entities);t<i.length;t++){var r=i[t];if("cloud"===r.platform&&"stt"===(0,A.m)(r.entity_id)){e=r.entity_id;break}}if(!e){var o,l=(0,g.A)(this._engines);try{for(l.s();!(o=l.n()).done;){var d,u=o.value;if(0!==(null==u||null===(d=u.supported_languages)||void 0===d?void 0:d.length)){e=u.engine_id;break}}}catch(h){l.e(h)}finally{l.f()}}}return e||(e=Z),(0,v.qy)(a||(a=q`
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
    `),this.label||this.hass.localize("ui.components.stt-picker.stt"),e,this.required,this.disabled,this._changed,b.d,this.required?v.s6:(0,v.qy)(n||(n=q`<ha-list-item .value=${0}>
              ${0}
            </ha-list-item>`),Z,this.hass.localize("ui.components.stt-picker.none")),this._engines.map((t=>{var i,a;if(t.deprecated&&t.engine_id!==e)return v.s6;if(t.engine_id.includes(".")){var n=this.hass.states[t.engine_id];a=n?(0,k.u)(n):t.engine_id}else a=t.name||t.engine_id;return(0,v.qy)(s||(s=q`<ha-list-item
            .value=${0}
            .disabled=${0}
          >
            ${0}
          </ha-list-item>`),t.engine_id,0===(null===(i=t.supported_languages)||void 0===i?void 0:i.length),a)})))}},{key:"willUpdate",value:function(e){(0,f.A)(t,"willUpdate",this,3)([e]),this.hasUpdated?e.has("language")&&this._debouncedUpdateEngines():this._updateEngines()}},{key:"_updateEngines",value:(i=(0,_.A)((0,p.A)().m((function e(){var t,i;return(0,p.A)().w((function(e){for(;;)switch(e.n){case 0:return e.n=1,(0,M.T)(this.hass,this.language,this.hass.config.country||void 0);case 1:if(this._engines=e.v.providers,this.value){e.n=2;break}return e.a(2);case 2:i=this._engines.find((e=>e.engine_id===this.value)),(0,y.r)(this,"supported-languages-changed",{value:null==i?void 0:i.supported_languages}),i&&0!==(null===(t=i.supported_languages)||void 0===t?void 0:t.length)||(this.value=void 0,(0,y.r)(this,"value-changed",{value:this.value}));case 3:return e.a(2)}}),e,this)}))),function(){return i.apply(this,arguments)})},{key:"_changed",value:function(e){var t,i=e.target;!this.hass||""===i.value||i.value===this.value||void 0===this.value&&i.value===Z||(this.value=i.value===Z?void 0:i.value,(0,y.r)(this,"value-changed",{value:this.value}),(0,y.r)(this,"supported-languages-changed",{value:null===(t=this._engines.find((e=>e.engine_id===this.value)))||void 0===t?void 0:t.supported_languages}))}}]);var i}(v.WF);m.styles=(0,v.AH)(r||(r=q`
    ha-select {
      width: 100%;
    }
  `)),(0,h.__decorate)([(0,c.MZ)()],m.prototype,"value",void 0),(0,h.__decorate)([(0,c.MZ)()],m.prototype,"label",void 0),(0,h.__decorate)([(0,c.MZ)()],m.prototype,"language",void 0),(0,h.__decorate)([(0,c.MZ)({attribute:!1})],m.prototype,"hass",void 0),(0,h.__decorate)([(0,c.MZ)({type:Boolean,reflect:!0})],m.prototype,"disabled",void 0),(0,h.__decorate)([(0,c.MZ)({type:Boolean})],m.prototype,"required",void 0),(0,h.__decorate)([(0,c.wk)()],m.prototype,"_engines",void 0),m=(0,h.__decorate)([(0,c.EM)("ha-stt-picker")],m);var w,E,x=e=>e,T=function(e){function t(){var e;(0,o.A)(this,t);for(var i=arguments.length,a=new Array(i),n=0;n<i;n++)a[n]=arguments[n];return(e=(0,d.A)(this,t,[].concat(a))).disabled=!1,e.required=!0,e}return(0,u.A)(t,e),(0,l.A)(t,[{key:"render",value:function(){var e,t;return(0,v.qy)(w||(w=x`<ha-stt-picker
      .hass=${0}
      .value=${0}
      .label=${0}
      .helper=${0}
      .language=${0}
      .disabled=${0}
      .required=${0}
    ></ha-stt-picker>`),this.hass,this.value,this.label,this.helper,(null===(e=this.selector.stt)||void 0===e?void 0:e.language)||(null===(t=this.context)||void 0===t?void 0:t.language),this.disabled,this.required)}}])}(v.WF);T.styles=(0,v.AH)(E||(E=x`
    ha-stt-picker {
      width: 100%;
    }
  `)),(0,h.__decorate)([(0,c.MZ)({attribute:!1})],T.prototype,"hass",void 0),(0,h.__decorate)([(0,c.MZ)({attribute:!1})],T.prototype,"selector",void 0),(0,h.__decorate)([(0,c.MZ)()],T.prototype,"value",void 0),(0,h.__decorate)([(0,c.MZ)()],T.prototype,"label",void 0),(0,h.__decorate)([(0,c.MZ)()],T.prototype,"helper",void 0),(0,h.__decorate)([(0,c.MZ)({type:Boolean})],T.prototype,"disabled",void 0),(0,h.__decorate)([(0,c.MZ)({type:Boolean})],T.prototype,"required",void 0),(0,h.__decorate)([(0,c.MZ)({attribute:!1})],T.prototype,"context",void 0),T=(0,h.__decorate)([(0,c.EM)("ha-selector-stt")],T)},61970:function(e,t,i){i.d(t,{T:function(){return a}});var a=(e,t,i)=>e.callWS({type:"stt/engine/list",language:t,country:i})}}]);
//# sourceMappingURL=4821.3e1af51e2596bbde.js.map
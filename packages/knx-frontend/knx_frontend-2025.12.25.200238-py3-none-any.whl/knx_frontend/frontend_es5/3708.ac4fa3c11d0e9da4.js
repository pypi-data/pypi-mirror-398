"use strict";(self.webpackChunkknx_frontend=self.webpackChunkknx_frontend||[]).push([["3708"],{42839:function(e,t,i){i.r(t),i.d(t,{HaTTSVoiceSelector:function(){return h}});var a,o,s=i(44734),n=i(56038),r=i(69683),l=i(6454),u=(i(28706),i(62826)),d=i(96196),c=i(77845),v=(i(10054),e=>e),h=function(e){function t(){var e;(0,s.A)(this,t);for(var i=arguments.length,a=new Array(i),o=0;o<i;o++)a[o]=arguments[o];return(e=(0,r.A)(this,t,[].concat(a))).disabled=!1,e.required=!0,e}return(0,l.A)(t,e),(0,n.A)(t,[{key:"render",value:function(){var e,t,i,o;return(0,d.qy)(a||(a=v`<ha-tts-voice-picker
      .hass=${0}
      .value=${0}
      .label=${0}
      .helper=${0}
      .language=${0}
      .engineId=${0}
      .disabled=${0}
      .required=${0}
    ></ha-tts-voice-picker>`),this.hass,this.value,this.label,this.helper,(null===(e=this.selector.tts_voice)||void 0===e?void 0:e.language)||(null===(t=this.context)||void 0===t?void 0:t.language),(null===(i=this.selector.tts_voice)||void 0===i?void 0:i.engineId)||(null===(o=this.context)||void 0===o?void 0:o.engineId),this.disabled,this.required)}}])}(d.WF);h.styles=(0,d.AH)(o||(o=v`
    ha-tts-picker {
      width: 100%;
    }
  `)),(0,u.__decorate)([(0,c.MZ)({attribute:!1})],h.prototype,"hass",void 0),(0,u.__decorate)([(0,c.MZ)({attribute:!1})],h.prototype,"selector",void 0),(0,u.__decorate)([(0,c.MZ)()],h.prototype,"value",void 0),(0,u.__decorate)([(0,c.MZ)()],h.prototype,"label",void 0),(0,u.__decorate)([(0,c.MZ)()],h.prototype,"helper",void 0),(0,u.__decorate)([(0,c.MZ)({type:Boolean})],h.prototype,"disabled",void 0),(0,u.__decorate)([(0,c.MZ)({type:Boolean})],h.prototype,"required",void 0),(0,u.__decorate)([(0,c.MZ)({attribute:!1})],h.prototype,"context",void 0),h=(0,u.__decorate)([(0,c.EM)("ha-selector-tts_voice")],h)},10054:function(e,t,i){var a,o,s,n,r=i(61397),l=i(50264),u=i(44734),d=i(56038),c=i(69683),v=i(6454),h=i(25460),_=(i(28706),i(50113),i(62062),i(18111),i(20116),i(61701),i(26099),i(62826)),p=i(96196),g=i(77845),y=i(92542),f=i(55124),b=i(40404),k=i(62146),$=(i(56565),i(69869),e=>e),M="__NONE_OPTION__",A=function(e){function t(){var e;(0,u.A)(this,t);for(var i=arguments.length,a=new Array(i),o=0;o<i;o++)a[o]=arguments[o];return(e=(0,c.A)(this,t,[].concat(a))).disabled=!1,e.required=!1,e._debouncedUpdateVoices=(0,b.s)((()=>e._updateVoices()),500),e}return(0,v.A)(t,e),(0,d.A)(t,[{key:"render",value:function(){var e,t;if(!this._voices)return p.s6;var i=null!==(e=this.value)&&void 0!==e?e:this.required?null===(t=this._voices[0])||void 0===t?void 0:t.voice_id:M;return(0,p.qy)(a||(a=$`
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
    `),this.label||this.hass.localize("ui.components.tts-voice-picker.voice"),i,this.required,this.disabled,this._changed,f.d,this.required?p.s6:(0,p.qy)(o||(o=$`<ha-list-item .value=${0}>
              ${0}
            </ha-list-item>`),M,this.hass.localize("ui.components.tts-voice-picker.none")),this._voices.map((e=>(0,p.qy)(s||(s=$`<ha-list-item .value=${0}>
              ${0}
            </ha-list-item>`),e.voice_id,e.name))))}},{key:"willUpdate",value:function(e){(0,h.A)(t,"willUpdate",this,3)([e]),this.hasUpdated?(e.has("language")||e.has("engineId"))&&this._debouncedUpdateVoices():this._updateVoices()}},{key:"_updateVoices",value:(i=(0,l.A)((0,r.A)().m((function e(){return(0,r.A)().w((function(e){for(;;)switch(e.n){case 0:if(this.engineId&&this.language){e.n=1;break}return this._voices=void 0,e.a(2);case 1:return e.n=2,(0,k.z3)(this.hass,this.engineId,this.language);case 2:if(this._voices=e.v.voices,this.value){e.n=3;break}return e.a(2);case 3:this._voices&&this._voices.find((e=>e.voice_id===this.value))||(this.value=void 0,(0,y.r)(this,"value-changed",{value:this.value}));case 4:return e.a(2)}}),e,this)}))),function(){return i.apply(this,arguments)})},{key:"updated",value:function(e){var i,a,o;((0,h.A)(t,"updated",this,3)([e]),e.has("_voices")&&(null===(i=this._select)||void 0===i?void 0:i.value)!==this.value)&&(null===(a=this._select)||void 0===a||a.layoutOptions(),(0,y.r)(this,"value-changed",{value:null===(o=this._select)||void 0===o?void 0:o.value}))}},{key:"_changed",value:function(e){var t=e.target;!this.hass||""===t.value||t.value===this.value||void 0===this.value&&t.value===M||(this.value=t.value===M?void 0:t.value,(0,y.r)(this,"value-changed",{value:this.value}))}}]);var i}(p.WF);A.styles=(0,p.AH)(n||(n=$`
    ha-select {
      width: 100%;
    }
  `)),(0,_.__decorate)([(0,g.MZ)()],A.prototype,"value",void 0),(0,_.__decorate)([(0,g.MZ)()],A.prototype,"label",void 0),(0,_.__decorate)([(0,g.MZ)({attribute:!1})],A.prototype,"engineId",void 0),(0,_.__decorate)([(0,g.MZ)()],A.prototype,"language",void 0),(0,_.__decorate)([(0,g.MZ)({attribute:!1})],A.prototype,"hass",void 0),(0,_.__decorate)([(0,g.MZ)({type:Boolean,reflect:!0})],A.prototype,"disabled",void 0),(0,_.__decorate)([(0,g.MZ)({type:Boolean})],A.prototype,"required",void 0),(0,_.__decorate)([(0,g.wk)()],A.prototype,"_voices",void 0),(0,_.__decorate)([(0,g.P)("ha-select")],A.prototype,"_select",void 0),A=(0,_.__decorate)([(0,g.EM)("ha-tts-voice-picker")],A)},62146:function(e,t,i){i.d(t,{EF:function(){return n},S_:function(){return a},Xv:function(){return r},ni:function(){return s},u1:function(){return l},z3:function(){return u}});var a=(e,t)=>e.callApi("POST","tts_get_url",t),o="media-source://tts/",s=e=>e.startsWith(o),n=e=>e.substring(19),r=(e,t,i)=>e.callWS({type:"tts/engine/list",language:t,country:i}),l=(e,t)=>e.callWS({type:"tts/engine/get",engine_id:t}),u=(e,t,i)=>e.callWS({type:"tts/engine/voices",engine_id:t,language:i})}}]);
//# sourceMappingURL=3708.ac4fa3c11d0e9da4.js.map
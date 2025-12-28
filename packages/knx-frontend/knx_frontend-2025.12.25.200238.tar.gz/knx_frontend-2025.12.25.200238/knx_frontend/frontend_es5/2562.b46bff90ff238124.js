"use strict";(self.webpackChunkknx_frontend=self.webpackChunkknx_frontend||[]).push([["2562"],{31747:function(e,t,i){i.a(e,(async function(e,s){try{i.d(t,{T:function(){return l}});var a=i(22),n=i(22786),r=e([a]);a=(r.then?(await r)():r)[0];var l=(e,t)=>{try{var i,s;return null!==(i=null===(s=o(t))||void 0===s?void 0:s.of(e))&&void 0!==i?i:e}catch(a){return e}},o=(0,n.A)((e=>new Intl.DisplayNames(e.language,{type:"language",fallback:"code"})));s()}catch(d){s(d)}}))},56528:function(e,t,i){i.a(e,(async function(e,t){try{var s=i(44734),a=i(56038),n=i(69683),r=i(6454),l=i(25460),o=(i(28706),i(50113),i(62062),i(18111),i(20116),i(61701),i(26099),i(62826)),d=i(96196),c=i(77845),p=i(92542),u=i(55124),h=i(31747),v=i(45369),_=(i(56565),i(69869),e([h]));h=(_.then?(await _)():_)[0];var g,b,y,f,j=e=>e,O="preferred",w="last_used",k=function(e){function t(){var e;(0,s.A)(this,t);for(var i=arguments.length,a=new Array(i),r=0;r<i;r++)a[r]=arguments[r];return(e=(0,n.A)(this,t,[].concat(a))).disabled=!1,e.required=!1,e.includeLastUsed=!1,e._preferredPipeline=null,e}return(0,r.A)(t,e),(0,a.A)(t,[{key:"_default",get:function(){return this.includeLastUsed?w:O}},{key:"render",value:function(){var e,t;if(!this._pipelines)return d.s6;var i=null!==(e=this.value)&&void 0!==e?e:this._default;return(0,d.qy)(g||(g=j`
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
        <ha-list-item .value=${0}>
          ${0}
        </ha-list-item>
        ${0}
      </ha-select>
    `),this.label||this.hass.localize("ui.components.pipeline-picker.pipeline"),i,this.required,this.disabled,this._changed,u.d,this.includeLastUsed?(0,d.qy)(b||(b=j`
              <ha-list-item .value=${0}>
                ${0}
              </ha-list-item>
            `),w,this.hass.localize("ui.components.pipeline-picker.last_used")):null,O,this.hass.localize("ui.components.pipeline-picker.preferred",{preferred:null===(t=this._pipelines.find((e=>e.id===this._preferredPipeline)))||void 0===t?void 0:t.name}),this._pipelines.map((e=>(0,d.qy)(y||(y=j`<ha-list-item .value=${0}>
              ${0}
              (${0})
            </ha-list-item>`),e.id,e.name,(0,h.T)(e.language,this.hass.locale)))))}},{key:"firstUpdated",value:function(e){(0,l.A)(t,"firstUpdated",this,3)([e]),(0,v.nx)(this.hass).then((e=>{this._pipelines=e.pipelines,this._preferredPipeline=e.preferred_pipeline}))}},{key:"_changed",value:function(e){var t=e.target;!this.hass||""===t.value||t.value===this.value||void 0===this.value&&t.value===this._default||(this.value=t.value===this._default?void 0:t.value,(0,p.r)(this,"value-changed",{value:this.value}))}}])}(d.WF);k.styles=(0,d.AH)(f||(f=j`
    ha-select {
      width: 100%;
    }
  `)),(0,o.__decorate)([(0,c.MZ)()],k.prototype,"value",void 0),(0,o.__decorate)([(0,c.MZ)()],k.prototype,"label",void 0),(0,o.__decorate)([(0,c.MZ)({attribute:!1})],k.prototype,"hass",void 0),(0,o.__decorate)([(0,c.MZ)({type:Boolean,reflect:!0})],k.prototype,"disabled",void 0),(0,o.__decorate)([(0,c.MZ)({type:Boolean})],k.prototype,"required",void 0),(0,o.__decorate)([(0,c.MZ)({attribute:!1})],k.prototype,"includeLastUsed",void 0),(0,o.__decorate)([(0,c.wk)()],k.prototype,"_pipelines",void 0),(0,o.__decorate)([(0,c.wk)()],k.prototype,"_preferredPipeline",void 0),k=(0,o.__decorate)([(0,c.EM)("ha-assist-pipeline-picker")],k),t()}catch($){t($)}}))},83353:function(e,t,i){i.a(e,(async function(e,s){try{i.r(t),i.d(t,{HaAssistPipelineSelector:function(){return g}});var a=i(44734),n=i(56038),r=i(69683),l=i(6454),o=(i(28706),i(62826)),d=i(96196),c=i(77845),p=i(56528),u=e([p]);p=(u.then?(await u)():u)[0];var h,v,_=e=>e,g=function(e){function t(){var e;(0,a.A)(this,t);for(var i=arguments.length,s=new Array(i),n=0;n<i;n++)s[n]=arguments[n];return(e=(0,r.A)(this,t,[].concat(s))).disabled=!1,e.required=!0,e}return(0,l.A)(t,e),(0,n.A)(t,[{key:"render",value:function(){var e;return(0,d.qy)(h||(h=_`
      <ha-assist-pipeline-picker
        .hass=${0}
        .value=${0}
        .label=${0}
        .helper=${0}
        .disabled=${0}
        .required=${0}
        .includeLastUsed=${0}
      ></ha-assist-pipeline-picker>
    `),this.hass,this.value,this.label,this.helper,this.disabled,this.required,Boolean(null===(e=this.selector.assist_pipeline)||void 0===e?void 0:e.include_last_used))}}])}(d.WF);g.styles=(0,d.AH)(v||(v=_`
    ha-conversation-agent-picker {
      width: 100%;
    }
  `)),(0,o.__decorate)([(0,c.MZ)({attribute:!1})],g.prototype,"hass",void 0),(0,o.__decorate)([(0,c.MZ)({attribute:!1})],g.prototype,"selector",void 0),(0,o.__decorate)([(0,c.MZ)()],g.prototype,"value",void 0),(0,o.__decorate)([(0,c.MZ)()],g.prototype,"label",void 0),(0,o.__decorate)([(0,c.MZ)()],g.prototype,"helper",void 0),(0,o.__decorate)([(0,c.MZ)({type:Boolean})],g.prototype,"disabled",void 0),(0,o.__decorate)([(0,c.MZ)({type:Boolean})],g.prototype,"required",void 0),g=(0,o.__decorate)([(0,c.EM)("ha-selector-assist_pipeline")],g),s()}catch(b){s(b)}}))},45369:function(e,t,i){i.d(t,{QC:function(){return a},ds:function(){return c},mp:function(){return l},nx:function(){return r},u6:function(){return o},vU:function(){return n},zn:function(){return d}});var s=i(94741),a=(i(28706),(e,t,i)=>"run-start"===t.type?e={init_options:i,stage:"ready",run:t.data,events:[t],started:new Date(t.timestamp)}:e?((e="wake_word-start"===t.type?Object.assign(Object.assign({},e),{},{stage:"wake_word",wake_word:Object.assign(Object.assign({},t.data),{},{done:!1})}):"wake_word-end"===t.type?Object.assign(Object.assign({},e),{},{wake_word:Object.assign(Object.assign(Object.assign({},e.wake_word),t.data),{},{done:!0})}):"stt-start"===t.type?Object.assign(Object.assign({},e),{},{stage:"stt",stt:Object.assign(Object.assign({},t.data),{},{done:!1})}):"stt-end"===t.type?Object.assign(Object.assign({},e),{},{stt:Object.assign(Object.assign(Object.assign({},e.stt),t.data),{},{done:!0})}):"intent-start"===t.type?Object.assign(Object.assign({},e),{},{stage:"intent",intent:Object.assign(Object.assign({},t.data),{},{done:!1})}):"intent-end"===t.type?Object.assign(Object.assign({},e),{},{intent:Object.assign(Object.assign(Object.assign({},e.intent),t.data),{},{done:!0})}):"tts-start"===t.type?Object.assign(Object.assign({},e),{},{stage:"tts",tts:Object.assign(Object.assign({},t.data),{},{done:!1})}):"tts-end"===t.type?Object.assign(Object.assign({},e),{},{tts:Object.assign(Object.assign(Object.assign({},e.tts),t.data),{},{done:!0})}):"run-end"===t.type?Object.assign(Object.assign({},e),{},{finished:new Date(t.timestamp),stage:"done"}):"error"===t.type?Object.assign(Object.assign({},e),{},{finished:new Date(t.timestamp),stage:"error",error:t.data}):Object.assign({},e)).events=[].concat((0,s.A)(e.events),[t]),e):void console.warn("Received unexpected event before receiving session",t)),n=(e,t,i)=>e.connection.subscribeMessage(t,Object.assign(Object.assign({},i),{},{type:"assist_pipeline/run"})),r=e=>e.callWS({type:"assist_pipeline/pipeline/list"}),l=(e,t)=>e.callWS({type:"assist_pipeline/pipeline/get",pipeline_id:t}),o=(e,t)=>e.callWS(Object.assign({type:"assist_pipeline/pipeline/create"},t)),d=(e,t,i)=>e.callWS(Object.assign({type:"assist_pipeline/pipeline/update",pipeline_id:t},i)),c=e=>e.callWS({type:"assist_pipeline/language/list"})}}]);
//# sourceMappingURL=2562.b46bff90ff238124.js.map
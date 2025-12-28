export const __webpack_id__="2562";export const __webpack_ids__=["2562"];export const __webpack_modules__={31747:function(e,t,i){i.a(e,(async function(e,s){try{i.d(t,{T:()=>p});var a=i(22),n=i(22786),r=e([a]);a=(r.then?(await r)():r)[0];const p=(e,t)=>{try{return d(t)?.of(e)??e}catch{return e}},d=(0,n.A)((e=>new Intl.DisplayNames(e.language,{type:"language",fallback:"code"})));s()}catch(p){s(p)}}))},56528:function(e,t,i){i.a(e,(async function(e,t){try{var s=i(62826),a=i(96196),n=i(77845),r=i(92542),p=i(55124),d=i(31747),l=i(45369),o=(i(56565),i(69869),e([d]));d=(o.then?(await o)():o)[0];const c="preferred",_="last_used";class u extends a.WF{get _default(){return this.includeLastUsed?_:c}render(){if(!this._pipelines)return a.s6;const e=this.value??this._default;return a.qy`
      <ha-select
        .label=${this.label||this.hass.localize("ui.components.pipeline-picker.pipeline")}
        .value=${e}
        .required=${this.required}
        .disabled=${this.disabled}
        @selected=${this._changed}
        @closed=${p.d}
        fixedMenuPosition
        naturalMenuWidth
      >
        ${this.includeLastUsed?a.qy`
              <ha-list-item .value=${_}>
                ${this.hass.localize("ui.components.pipeline-picker.last_used")}
              </ha-list-item>
            `:null}
        <ha-list-item .value=${c}>
          ${this.hass.localize("ui.components.pipeline-picker.preferred",{preferred:this._pipelines.find((e=>e.id===this._preferredPipeline))?.name})}
        </ha-list-item>
        ${this._pipelines.map((e=>a.qy`<ha-list-item .value=${e.id}>
              ${e.name}
              (${(0,d.T)(e.language,this.hass.locale)})
            </ha-list-item>`))}
      </ha-select>
    `}firstUpdated(e){super.firstUpdated(e),(0,l.nx)(this.hass).then((e=>{this._pipelines=e.pipelines,this._preferredPipeline=e.preferred_pipeline}))}_changed(e){const t=e.target;!this.hass||""===t.value||t.value===this.value||void 0===this.value&&t.value===this._default||(this.value=t.value===this._default?void 0:t.value,(0,r.r)(this,"value-changed",{value:this.value}))}constructor(...e){super(...e),this.disabled=!1,this.required=!1,this.includeLastUsed=!1,this._preferredPipeline=null}}u.styles=a.AH`
    ha-select {
      width: 100%;
    }
  `,(0,s.__decorate)([(0,n.MZ)()],u.prototype,"value",void 0),(0,s.__decorate)([(0,n.MZ)()],u.prototype,"label",void 0),(0,s.__decorate)([(0,n.MZ)({attribute:!1})],u.prototype,"hass",void 0),(0,s.__decorate)([(0,n.MZ)({type:Boolean,reflect:!0})],u.prototype,"disabled",void 0),(0,s.__decorate)([(0,n.MZ)({type:Boolean})],u.prototype,"required",void 0),(0,s.__decorate)([(0,n.MZ)({attribute:!1})],u.prototype,"includeLastUsed",void 0),(0,s.__decorate)([(0,n.wk)()],u.prototype,"_pipelines",void 0),(0,s.__decorate)([(0,n.wk)()],u.prototype,"_preferredPipeline",void 0),u=(0,s.__decorate)([(0,n.EM)("ha-assist-pipeline-picker")],u),t()}catch(c){t(c)}}))},83353:function(e,t,i){i.a(e,(async function(e,s){try{i.r(t),i.d(t,{HaAssistPipelineSelector:()=>l});var a=i(62826),n=i(96196),r=i(77845),p=i(56528),d=e([p]);p=(d.then?(await d)():d)[0];class l extends n.WF{render(){return n.qy`
      <ha-assist-pipeline-picker
        .hass=${this.hass}
        .value=${this.value}
        .label=${this.label}
        .helper=${this.helper}
        .disabled=${this.disabled}
        .required=${this.required}
        .includeLastUsed=${Boolean(this.selector.assist_pipeline?.include_last_used)}
      ></ha-assist-pipeline-picker>
    `}constructor(...e){super(...e),this.disabled=!1,this.required=!0}}l.styles=n.AH`
    ha-conversation-agent-picker {
      width: 100%;
    }
  `,(0,a.__decorate)([(0,r.MZ)({attribute:!1})],l.prototype,"hass",void 0),(0,a.__decorate)([(0,r.MZ)({attribute:!1})],l.prototype,"selector",void 0),(0,a.__decorate)([(0,r.MZ)()],l.prototype,"value",void 0),(0,a.__decorate)([(0,r.MZ)()],l.prototype,"label",void 0),(0,a.__decorate)([(0,r.MZ)()],l.prototype,"helper",void 0),(0,a.__decorate)([(0,r.MZ)({type:Boolean})],l.prototype,"disabled",void 0),(0,a.__decorate)([(0,r.MZ)({type:Boolean})],l.prototype,"required",void 0),l=(0,a.__decorate)([(0,r.EM)("ha-selector-assist_pipeline")],l),s()}catch(l){s(l)}}))},45369:function(e,t,i){i.d(t,{QC:()=>s,ds:()=>l,mp:()=>r,nx:()=>n,u6:()=>p,vU:()=>a,zn:()=>d});const s=(e,t,i)=>"run-start"===t.type?e={init_options:i,stage:"ready",run:t.data,events:[t],started:new Date(t.timestamp)}:e?((e="wake_word-start"===t.type?{...e,stage:"wake_word",wake_word:{...t.data,done:!1}}:"wake_word-end"===t.type?{...e,wake_word:{...e.wake_word,...t.data,done:!0}}:"stt-start"===t.type?{...e,stage:"stt",stt:{...t.data,done:!1}}:"stt-end"===t.type?{...e,stt:{...e.stt,...t.data,done:!0}}:"intent-start"===t.type?{...e,stage:"intent",intent:{...t.data,done:!1}}:"intent-end"===t.type?{...e,intent:{...e.intent,...t.data,done:!0}}:"tts-start"===t.type?{...e,stage:"tts",tts:{...t.data,done:!1}}:"tts-end"===t.type?{...e,tts:{...e.tts,...t.data,done:!0}}:"run-end"===t.type?{...e,finished:new Date(t.timestamp),stage:"done"}:"error"===t.type?{...e,finished:new Date(t.timestamp),stage:"error",error:t.data}:{...e}).events=[...e.events,t],e):void console.warn("Received unexpected event before receiving session",t),a=(e,t,i)=>e.connection.subscribeMessage(t,{...i,type:"assist_pipeline/run"}),n=e=>e.callWS({type:"assist_pipeline/pipeline/list"}),r=(e,t)=>e.callWS({type:"assist_pipeline/pipeline/get",pipeline_id:t}),p=(e,t)=>e.callWS({type:"assist_pipeline/pipeline/create",...t}),d=(e,t,i)=>e.callWS({type:"assist_pipeline/pipeline/update",pipeline_id:t,...i}),l=e=>e.callWS({type:"assist_pipeline/language/list"})}};
//# sourceMappingURL=2562.d0e650e2216b3e10.js.map
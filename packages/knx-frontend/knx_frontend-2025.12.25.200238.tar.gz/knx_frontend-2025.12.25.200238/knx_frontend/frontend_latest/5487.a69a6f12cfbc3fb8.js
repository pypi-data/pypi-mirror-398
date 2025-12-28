export const __webpack_id__="5487";export const __webpack_ids__=["5487"];export const __webpack_modules__={34818:function(e,t,i){i.r(t),i.d(t,{HaTTSSelector:()=>c});var s=i(62826),a=i(96196),n=i(77845),o=i(92542),d=i(55124),r=i(91889),l=i(40404),u=i(62146),h=(i(56565),i(69869),i(41144));const _="__NONE_OPTION__";class p extends a.WF{render(){if(!this._engines)return a.s6;let e=this.value;if(!e&&this.required){for(const t of Object.values(this.hass.entities))if("cloud"===t.platform&&"tts"===(0,h.m)(t.entity_id)){e=t.entity_id;break}if(!e)for(const t of this._engines)if(0!==t?.supported_languages?.length){e=t.engine_id;break}}return e||(e=_),a.qy`
      <ha-select
        .label=${this.label||this.hass.localize("ui.components.tts-picker.tts")}
        .value=${e}
        .required=${this.required}
        .disabled=${this.disabled}
        @selected=${this._changed}
        @closed=${d.d}
        fixedMenuPosition
        naturalMenuWidth
      >
        ${this.required?a.s6:a.qy`<ha-list-item .value=${_}>
              ${this.hass.localize("ui.components.tts-picker.none")}
            </ha-list-item>`}
        ${this._engines.map((t=>{if(t.deprecated&&t.engine_id!==e)return a.s6;let i;if(t.engine_id.includes(".")){const e=this.hass.states[t.engine_id];i=e?(0,r.u)(e):t.engine_id}else i=t.name||t.engine_id;return a.qy`<ha-list-item
            .value=${t.engine_id}
            .disabled=${0===t.supported_languages?.length}
          >
            ${i}
          </ha-list-item>`}))}
      </ha-select>
    `}willUpdate(e){super.willUpdate(e),this.hasUpdated?e.has("language")&&this._debouncedUpdateEngines():this._updateEngines()}async _updateEngines(){if(this._engines=(await(0,u.Xv)(this.hass,this.language,this.hass.config.country||void 0)).providers,!this.value)return;const e=this._engines.find((e=>e.engine_id===this.value));(0,o.r)(this,"supported-languages-changed",{value:e?.supported_languages}),e&&0!==e.supported_languages?.length||(this.value=void 0,(0,o.r)(this,"value-changed",{value:this.value}))}_changed(e){const t=e.target;!this.hass||""===t.value||t.value===this.value||void 0===this.value&&t.value===_||(this.value=t.value===_?void 0:t.value,(0,o.r)(this,"value-changed",{value:this.value}),(0,o.r)(this,"supported-languages-changed",{value:this._engines.find((e=>e.engine_id===this.value))?.supported_languages}))}constructor(...e){super(...e),this.disabled=!1,this.required=!1,this._debouncedUpdateEngines=(0,l.s)((()=>this._updateEngines()),500)}}p.styles=a.AH`
    ha-select {
      width: 100%;
    }
  `,(0,s.__decorate)([(0,n.MZ)()],p.prototype,"value",void 0),(0,s.__decorate)([(0,n.MZ)()],p.prototype,"label",void 0),(0,s.__decorate)([(0,n.MZ)()],p.prototype,"language",void 0),(0,s.__decorate)([(0,n.MZ)({attribute:!1})],p.prototype,"hass",void 0),(0,s.__decorate)([(0,n.MZ)({type:Boolean,reflect:!0})],p.prototype,"disabled",void 0),(0,s.__decorate)([(0,n.MZ)({type:Boolean})],p.prototype,"required",void 0),(0,s.__decorate)([(0,n.wk)()],p.prototype,"_engines",void 0),p=(0,s.__decorate)([(0,n.EM)("ha-tts-picker")],p);class c extends a.WF{render(){return a.qy`<ha-tts-picker
      .hass=${this.hass}
      .value=${this.value}
      .label=${this.label}
      .helper=${this.helper}
      .language=${this.selector.tts?.language||this.context?.language}
      .disabled=${this.disabled}
      .required=${this.required}
    ></ha-tts-picker>`}constructor(...e){super(...e),this.disabled=!1,this.required=!0}}c.styles=a.AH`
    ha-tts-picker {
      width: 100%;
    }
  `,(0,s.__decorate)([(0,n.MZ)({attribute:!1})],c.prototype,"hass",void 0),(0,s.__decorate)([(0,n.MZ)({attribute:!1})],c.prototype,"selector",void 0),(0,s.__decorate)([(0,n.MZ)()],c.prototype,"value",void 0),(0,s.__decorate)([(0,n.MZ)()],c.prototype,"label",void 0),(0,s.__decorate)([(0,n.MZ)()],c.prototype,"helper",void 0),(0,s.__decorate)([(0,n.MZ)({type:Boolean})],c.prototype,"disabled",void 0),(0,s.__decorate)([(0,n.MZ)({type:Boolean})],c.prototype,"required",void 0),(0,s.__decorate)([(0,n.MZ)({attribute:!1})],c.prototype,"context",void 0),c=(0,s.__decorate)([(0,n.EM)("ha-selector-tts")],c)},62146:function(e,t,i){i.d(t,{EF:()=>o,S_:()=>s,Xv:()=>d,ni:()=>n,u1:()=>r,z3:()=>l});const s=(e,t)=>e.callApi("POST","tts_get_url",t),a="media-source://tts/",n=e=>e.startsWith(a),o=e=>e.substring(19),d=(e,t,i)=>e.callWS({type:"tts/engine/list",language:t,country:i}),r=(e,t)=>e.callWS({type:"tts/engine/get",engine_id:t}),l=(e,t,i)=>e.callWS({type:"tts/engine/voices",engine_id:t,language:i})}};
//# sourceMappingURL=5487.a69a6f12cfbc3fb8.js.map
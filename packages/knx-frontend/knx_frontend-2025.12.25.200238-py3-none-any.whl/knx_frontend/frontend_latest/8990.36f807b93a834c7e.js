export const __webpack_id__="8990";export const __webpack_ids__=["8990"];export const __webpack_modules__={1629:function(e,t,o){o.r(t),o.d(t,{HaConfigEntrySelector:()=>c});var i=o(62826),a=o(96196),r=o(77845),s=o(92542),n=o(25749),d=o(3950),l=o(84125),h=o(76681);o(34887),o(94343);class _ extends a.WF{open(){this._comboBox?.open()}focus(){this._comboBox?.focus()}firstUpdated(){this._getConfigEntries()}render(){return this._configEntries?a.qy`
      <ha-combo-box
        .hass=${this.hass}
        .label=${void 0===this.label&&this.hass?this.hass.localize("ui.components.config-entry-picker.config_entry"):this.label}
        .value=${this._value}
        .required=${this.required}
        .disabled=${this.disabled}
        .helper=${this.helper}
        .renderer=${this._rowRenderer}
        .items=${this._configEntries}
        item-value-path="entry_id"
        item-id-path="entry_id"
        item-label-path="title"
        @value-changed=${this._valueChanged}
      ></ha-combo-box>
    `:a.s6}_onImageLoad(e){e.target.style.visibility="initial"}_onImageError(e){e.target.style.visibility="hidden"}async _getConfigEntries(){(0,d.VN)(this.hass,{type:["device","hub","service"],domain:this.integration}).then((e=>{this._configEntries=e.map((e=>({...e,localized_domain_name:(0,l.p$)(this.hass.localize,e.domain)}))).sort(((e,t)=>(0,n.SH)(e.localized_domain_name+e.title,t.localized_domain_name+t.title,this.hass.locale.language)))}))}get _value(){return this.value||""}_valueChanged(e){e.stopPropagation();const t=e.detail.value;t!==this._value&&this._setValue(t)}_setValue(e){this.value=e,setTimeout((()=>{(0,s.r)(this,"value-changed",{value:e}),(0,s.r)(this,"change")}),0)}constructor(...e){super(...e),this.value="",this.disabled=!1,this.required=!1,this._rowRenderer=e=>a.qy`
    <ha-combo-box-item type="button">
      <span slot="headline">
        ${e.title||this.hass.localize("ui.panel.config.integrations.config_entry.unnamed_entry")}
      </span>
      <span slot="supporting-text">${e.localized_domain_name}</span>
      <img
        alt=""
        slot="start"
        src=${(0,h.MR)({domain:e.domain,type:"icon",darkOptimized:this.hass.themes?.darkMode})}
        crossorigin="anonymous"
        referrerpolicy="no-referrer"
        @error=${this._onImageError}
        @load=${this._onImageLoad}
      />
    </ha-combo-box-item>
  `}}(0,i.__decorate)([(0,r.MZ)()],_.prototype,"integration",void 0),(0,i.__decorate)([(0,r.MZ)()],_.prototype,"label",void 0),(0,i.__decorate)([(0,r.MZ)()],_.prototype,"value",void 0),(0,i.__decorate)([(0,r.MZ)()],_.prototype,"helper",void 0),(0,i.__decorate)([(0,r.wk)()],_.prototype,"_configEntries",void 0),(0,i.__decorate)([(0,r.MZ)({type:Boolean})],_.prototype,"disabled",void 0),(0,i.__decorate)([(0,r.MZ)({type:Boolean})],_.prototype,"required",void 0),(0,i.__decorate)([(0,r.P)("ha-combo-box")],_.prototype,"_comboBox",void 0),_=(0,i.__decorate)([(0,r.EM)("ha-config-entry-picker")],_);class c extends a.WF{render(){return a.qy`<ha-config-entry-picker
      .hass=${this.hass}
      .value=${this.value}
      .label=${this.label}
      .helper=${this.helper}
      .disabled=${this.disabled}
      .required=${this.required}
      .integration=${this.selector.config_entry?.integration}
      allow-custom-entity
    ></ha-config-entry-picker>`}constructor(...e){super(...e),this.disabled=!1,this.required=!0}}c.styles=a.AH`
    ha-config-entry-picker {
      width: 100%;
    }
  `,(0,i.__decorate)([(0,r.MZ)({attribute:!1})],c.prototype,"hass",void 0),(0,i.__decorate)([(0,r.MZ)({attribute:!1})],c.prototype,"selector",void 0),(0,i.__decorate)([(0,r.MZ)()],c.prototype,"value",void 0),(0,i.__decorate)([(0,r.MZ)()],c.prototype,"label",void 0),(0,i.__decorate)([(0,r.MZ)()],c.prototype,"helper",void 0),(0,i.__decorate)([(0,r.MZ)({type:Boolean})],c.prototype,"disabled",void 0),(0,i.__decorate)([(0,r.MZ)({type:Boolean})],c.prototype,"required",void 0),c=(0,i.__decorate)([(0,r.EM)("ha-selector-config_entry")],c)},76681:function(e,t,o){o.d(t,{MR:()=>i,a_:()=>a,bg:()=>r});const i=e=>`https://brands.home-assistant.io/${e.brand?"brands/":""}${e.useFallback?"_/":""}${e.domain}/${e.darkOptimized?"dark_":""}${e.type}.png`,a=e=>e.split("/")[4],r=e=>e.startsWith("https://brands.home-assistant.io/")}};
//# sourceMappingURL=8990.36f807b93a834c7e.js.map
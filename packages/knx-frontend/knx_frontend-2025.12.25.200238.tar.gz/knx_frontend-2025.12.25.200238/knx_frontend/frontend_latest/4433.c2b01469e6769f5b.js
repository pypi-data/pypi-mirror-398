export const __webpack_id__="4433";export const __webpack_ids__=["4433"];export const __webpack_modules__={41944:function(e,o,t){t.r(o),t.d(o,{HaAddonSelector:()=>c});var s=t(62826),a=t(96196),r=t(77845),i=t(92209),d=t(92542),n=t(25749),l=t(34402);t(17963),t(34887),t(94343);const p=e=>a.qy`
  <ha-combo-box-item type="button">
    <span slot="headline">${e.name}</span>
    <span slot="supporting-text">${e.slug}</span>
    ${e.icon?a.qy`
          <img
            alt=""
            slot="start"
            .src="/api/hassio/addons/${e.slug}/icon"
          />
        `:a.s6}
  </ha-combo-box-item>
`;class h extends a.WF{open(){this._comboBox?.open()}focus(){this._comboBox?.focus()}firstUpdated(){this._getAddons()}render(){return this._error?a.qy`<ha-alert alert-type="error">${this._error}</ha-alert>`:this._addons?a.qy`
      <ha-combo-box
        .hass=${this.hass}
        .label=${void 0===this.label&&this.hass?this.hass.localize("ui.components.addon-picker.addon"):this.label}
        .value=${this._value}
        .required=${this.required}
        .disabled=${this.disabled}
        .helper=${this.helper}
        .renderer=${p}
        .items=${this._addons}
        item-value-path="slug"
        item-id-path="slug"
        item-label-path="name"
        @value-changed=${this._addonChanged}
      ></ha-combo-box>
    `:a.s6}async _getAddons(){try{if((0,i.x)(this.hass,"hassio")){const e=await(0,l.b3)(this.hass);this._addons=e.addons.filter((e=>e.version)).sort(((e,o)=>(0,n.xL)(e.name,o.name,this.hass.locale.language)))}else this._error=this.hass.localize("ui.components.addon-picker.error.no_supervisor")}catch(e){this._error=this.hass.localize("ui.components.addon-picker.error.fetch_addons")}}get _value(){return this.value||""}_addonChanged(e){e.stopPropagation();const o=e.detail.value;o!==this._value&&this._setValue(o)}_setValue(e){this.value=e,setTimeout((()=>{(0,d.r)(this,"value-changed",{value:e}),(0,d.r)(this,"change")}),0)}constructor(...e){super(...e),this.value="",this.disabled=!1,this.required=!1}}(0,s.__decorate)([(0,r.MZ)()],h.prototype,"label",void 0),(0,s.__decorate)([(0,r.MZ)()],h.prototype,"value",void 0),(0,s.__decorate)([(0,r.MZ)()],h.prototype,"helper",void 0),(0,s.__decorate)([(0,r.wk)()],h.prototype,"_addons",void 0),(0,s.__decorate)([(0,r.MZ)({type:Boolean})],h.prototype,"disabled",void 0),(0,s.__decorate)([(0,r.MZ)({type:Boolean})],h.prototype,"required",void 0),(0,s.__decorate)([(0,r.P)("ha-combo-box")],h.prototype,"_comboBox",void 0),(0,s.__decorate)([(0,r.wk)()],h.prototype,"_error",void 0),h=(0,s.__decorate)([(0,r.EM)("ha-addon-picker")],h);class c extends a.WF{render(){return a.qy`<ha-addon-picker
      .hass=${this.hass}
      .value=${this.value}
      .label=${this.label}
      .helper=${this.helper}
      .disabled=${this.disabled}
      .required=${this.required}
      allow-custom-entity
    ></ha-addon-picker>`}constructor(...e){super(...e),this.disabled=!1,this.required=!0}}c.styles=a.AH`
    ha-addon-picker {
      width: 100%;
    }
  `,(0,s.__decorate)([(0,r.MZ)({attribute:!1})],c.prototype,"hass",void 0),(0,s.__decorate)([(0,r.MZ)({attribute:!1})],c.prototype,"selector",void 0),(0,s.__decorate)([(0,r.MZ)()],c.prototype,"value",void 0),(0,s.__decorate)([(0,r.MZ)()],c.prototype,"label",void 0),(0,s.__decorate)([(0,r.MZ)()],c.prototype,"helper",void 0),(0,s.__decorate)([(0,r.MZ)({type:Boolean})],c.prototype,"disabled",void 0),(0,s.__decorate)([(0,r.MZ)({type:Boolean})],c.prototype,"required",void 0),c=(0,s.__decorate)([(0,r.EM)("ha-selector-addon")],c)},34402:function(e,o,t){t.d(o,{xG:()=>d,b3:()=>r,eK:()=>i});var s=t(53045),a=t(95260);const r=async e=>(0,s.v)(e.config.version,2021,2,4)?e.callWS({type:"supervisor/api",endpoint:"/addons",method:"get"}):(0,a.PS)(await e.callApi("GET","hassio/addons")),i=async(e,o)=>(0,s.v)(e.config.version,2021,2,4)?e.callWS({type:"supervisor/api",endpoint:`/addons/${o}/start`,method:"post",timeout:null}):e.callApi("POST",`hassio/addons/${o}/start`),d=async(e,o)=>{(0,s.v)(e.config.version,2021,2,4)?await e.callWS({type:"supervisor/api",endpoint:`/addons/${o}/install`,method:"post",timeout:null}):await e.callApi("POST",`hassio/addons/${o}/install`)}},95260:function(e,o,t){t.d(o,{PS:()=>s,VR:()=>a});const s=e=>e.data,a=e=>"object"==typeof e?"object"==typeof e.body?e.body.message||"Unknown error, see supervisor logs":e.body||e.message||"Unknown error, see supervisor logs":e;new Set([502,503,504])}};
//# sourceMappingURL=4433.c2b01469e6769f5b.js.map
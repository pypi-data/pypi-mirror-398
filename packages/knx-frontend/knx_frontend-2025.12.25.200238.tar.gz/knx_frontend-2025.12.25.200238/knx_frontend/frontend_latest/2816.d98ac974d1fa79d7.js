export const __webpack_id__="2816";export const __webpack_ids__=["2816"];export const __webpack_modules__={60977:function(e,t,i){i.a(e,(async function(e,t){try{var s=i(62826),r=i(96196),o=i(77845),a=i(22786),c=i(92542),d=i(56403),n=i(16727),l=i(13877),h=i(3950),p=i(1491),u=i(76681),v=i(96943),_=e([v]);v=(_.then?(await _)():_)[0];class y extends r.WF{firstUpdated(e){super.firstUpdated(e),this._loadConfigEntries()}async _loadConfigEntries(){const e=await(0,h.VN)(this.hass);this._configEntryLookup=Object.fromEntries(e.map((e=>[e.entry_id,e])))}render(){const e=this.placeholder??this.hass.localize("ui.components.device-picker.placeholder"),t=this._valueRenderer(this._configEntryLookup);return r.qy`
      <ha-generic-picker
        .hass=${this.hass}
        .autofocus=${this.autofocus}
        .label=${this.label}
        .searchLabel=${this.searchLabel}
        .notFoundLabel=${this._notFoundLabel}
        .emptyLabel=${this.hass.localize("ui.components.device-picker.no_devices")}
        .placeholder=${e}
        .value=${this.value}
        .rowRenderer=${this._rowRenderer}
        .getItems=${this._getItems}
        .hideClearIcon=${this.hideClearIcon}
        .valueRenderer=${t}
        @value-changed=${this._valueChanged}
      >
      </ha-generic-picker>
    `}async open(){await this.updateComplete,await(this._picker?.open())}_valueChanged(e){e.stopPropagation();const t=e.detail.value;this.value=t,(0,c.r)(this,"value-changed",{value:t})}constructor(...e){super(...e),this.autofocus=!1,this.disabled=!1,this.required=!1,this.hideClearIcon=!1,this._configEntryLookup={},this._getDevicesMemoized=(0,a.A)(p.oG),this._getItems=()=>this._getDevicesMemoized(this.hass,this._configEntryLookup,this.includeDomains,this.excludeDomains,this.includeDeviceClasses,this.deviceFilter,this.entityFilter,this.excludeDevices,this.value),this._valueRenderer=(0,a.A)((e=>t=>{const i=t,s=this.hass.devices[i];if(!s)return r.qy`<span slot="headline">${i}</span>`;const{area:o}=(0,l.w)(s,this.hass),a=s?(0,n.xn)(s):void 0,c=o?(0,d.A)(o):void 0,h=s.primary_config_entry?e[s.primary_config_entry]:void 0;return r.qy`
        ${h?r.qy`<img
              slot="start"
              alt=""
              crossorigin="anonymous"
              referrerpolicy="no-referrer"
              src=${(0,u.MR)({domain:h.domain,type:"icon",darkOptimized:this.hass.themes?.darkMode})}
            />`:r.s6}
        <span slot="headline">${a}</span>
        <span slot="supporting-text">${c}</span>
      `})),this._rowRenderer=e=>r.qy`
    <ha-combo-box-item type="button">
      ${e.domain?r.qy`
            <img
              slot="start"
              alt=""
              crossorigin="anonymous"
              referrerpolicy="no-referrer"
              src=${(0,u.MR)({domain:e.domain,type:"icon",darkOptimized:this.hass.themes.darkMode})}
            />
          `:r.s6}

      <span slot="headline">${e.primary}</span>
      ${e.secondary?r.qy`<span slot="supporting-text">${e.secondary}</span>`:r.s6}
      ${e.domain_name?r.qy`
            <div slot="trailing-supporting-text" class="domain">
              ${e.domain_name}
            </div>
          `:r.s6}
    </ha-combo-box-item>
  `,this._notFoundLabel=e=>this.hass.localize("ui.components.device-picker.no_match",{term:r.qy`<b>‘${e}’</b>`})}}(0,s.__decorate)([(0,o.MZ)({attribute:!1})],y.prototype,"hass",void 0),(0,s.__decorate)([(0,o.MZ)({type:Boolean})],y.prototype,"autofocus",void 0),(0,s.__decorate)([(0,o.MZ)({type:Boolean})],y.prototype,"disabled",void 0),(0,s.__decorate)([(0,o.MZ)({type:Boolean})],y.prototype,"required",void 0),(0,s.__decorate)([(0,o.MZ)()],y.prototype,"label",void 0),(0,s.__decorate)([(0,o.MZ)()],y.prototype,"value",void 0),(0,s.__decorate)([(0,o.MZ)()],y.prototype,"helper",void 0),(0,s.__decorate)([(0,o.MZ)()],y.prototype,"placeholder",void 0),(0,s.__decorate)([(0,o.MZ)({type:String,attribute:"search-label"})],y.prototype,"searchLabel",void 0),(0,s.__decorate)([(0,o.MZ)({attribute:!1,type:Array})],y.prototype,"createDomains",void 0),(0,s.__decorate)([(0,o.MZ)({type:Array,attribute:"include-domains"})],y.prototype,"includeDomains",void 0),(0,s.__decorate)([(0,o.MZ)({type:Array,attribute:"exclude-domains"})],y.prototype,"excludeDomains",void 0),(0,s.__decorate)([(0,o.MZ)({type:Array,attribute:"include-device-classes"})],y.prototype,"includeDeviceClasses",void 0),(0,s.__decorate)([(0,o.MZ)({type:Array,attribute:"exclude-devices"})],y.prototype,"excludeDevices",void 0),(0,s.__decorate)([(0,o.MZ)({attribute:!1})],y.prototype,"deviceFilter",void 0),(0,s.__decorate)([(0,o.MZ)({attribute:!1})],y.prototype,"entityFilter",void 0),(0,s.__decorate)([(0,o.MZ)({attribute:"hide-clear-icon",type:Boolean})],y.prototype,"hideClearIcon",void 0),(0,s.__decorate)([(0,o.P)("ha-generic-picker")],y.prototype,"_picker",void 0),(0,s.__decorate)([(0,o.wk)()],y.prototype,"_configEntryLookup",void 0),y=(0,s.__decorate)([(0,o.EM)("ha-device-picker")],y),t()}catch(y){t(y)}}))},55212:function(e,t,i){i.a(e,(async function(e,t){try{var s=i(62826),r=i(96196),o=i(77845),a=i(92542),c=i(60977),d=e([c]);c=(d.then?(await d)():d)[0];class n extends r.WF{render(){if(!this.hass)return r.s6;const e=this._currentDevices;return r.qy`
      ${e.map((e=>r.qy`
          <div>
            <ha-device-picker
              allow-custom-entity
              .curValue=${e}
              .hass=${this.hass}
              .deviceFilter=${this.deviceFilter}
              .entityFilter=${this.entityFilter}
              .includeDomains=${this.includeDomains}
              .excludeDomains=${this.excludeDomains}
              .includeDeviceClasses=${this.includeDeviceClasses}
              .value=${e}
              .label=${this.pickedDeviceLabel}
              .disabled=${this.disabled}
              @value-changed=${this._deviceChanged}
            ></ha-device-picker>
          </div>
        `))}
      <div>
        <ha-device-picker
          allow-custom-entity
          .hass=${this.hass}
          .helper=${this.helper}
          .deviceFilter=${this.deviceFilter}
          .entityFilter=${this.entityFilter}
          .includeDomains=${this.includeDomains}
          .excludeDomains=${this.excludeDomains}
          .excludeDevices=${e}
          .includeDeviceClasses=${this.includeDeviceClasses}
          .label=${this.pickDeviceLabel}
          .disabled=${this.disabled}
          .required=${this.required&&!e.length}
          @value-changed=${this._addDevice}
        ></ha-device-picker>
      </div>
    `}get _currentDevices(){return this.value||[]}async _updateDevices(e){(0,a.r)(this,"value-changed",{value:e}),this.value=e}_deviceChanged(e){e.stopPropagation();const t=e.currentTarget.curValue,i=e.detail.value;i!==t&&(void 0===i?this._updateDevices(this._currentDevices.filter((e=>e!==t))):this._updateDevices(this._currentDevices.map((e=>e===t?i:e))))}async _addDevice(e){e.stopPropagation();const t=e.detail.value;if(e.currentTarget.value="",!t)return;const i=this._currentDevices;i.includes(t)||this._updateDevices([...i,t])}constructor(...e){super(...e),this.disabled=!1,this.required=!1}}n.styles=r.AH`
    div {
      margin-top: 8px;
    }
  `,(0,s.__decorate)([(0,o.MZ)({attribute:!1})],n.prototype,"hass",void 0),(0,s.__decorate)([(0,o.MZ)({type:Array})],n.prototype,"value",void 0),(0,s.__decorate)([(0,o.MZ)()],n.prototype,"helper",void 0),(0,s.__decorate)([(0,o.MZ)({type:Boolean})],n.prototype,"disabled",void 0),(0,s.__decorate)([(0,o.MZ)({type:Boolean})],n.prototype,"required",void 0),(0,s.__decorate)([(0,o.MZ)({type:Array,attribute:"include-domains"})],n.prototype,"includeDomains",void 0),(0,s.__decorate)([(0,o.MZ)({type:Array,attribute:"exclude-domains"})],n.prototype,"excludeDomains",void 0),(0,s.__decorate)([(0,o.MZ)({type:Array,attribute:"include-device-classes"})],n.prototype,"includeDeviceClasses",void 0),(0,s.__decorate)([(0,o.MZ)({attribute:"picked-device-label"})],n.prototype,"pickedDeviceLabel",void 0),(0,s.__decorate)([(0,o.MZ)({attribute:"pick-device-label"})],n.prototype,"pickDeviceLabel",void 0),(0,s.__decorate)([(0,o.MZ)({attribute:!1})],n.prototype,"deviceFilter",void 0),(0,s.__decorate)([(0,o.MZ)({attribute:!1})],n.prototype,"entityFilter",void 0),n=(0,s.__decorate)([(0,o.EM)("ha-devices-picker")],n),t()}catch(n){t(n)}}))},95907:function(e,t,i){i.a(e,(async function(e,s){try{i.r(t),i.d(t,{HaDeviceSelector:()=>b});var r=i(62826),o=i(96196),a=i(77845),c=i(22786),d=i(55376),n=i(92542),l=i(1491),h=i(28441),p=i(3950),u=i(82694),v=i(60977),_=i(55212),y=e([v,_]);[v,_]=y.then?(await y)():y;class b extends o.WF{_hasIntegration(e){return e.device?.filter&&(0,d.e)(e.device.filter).some((e=>e.integration))||e.device?.entity&&(0,d.e)(e.device.entity).some((e=>e.integration))}willUpdate(e){e.get("selector")&&void 0!==this.value&&(this.selector.device?.multiple&&!Array.isArray(this.value)?(this.value=[this.value],(0,n.r)(this,"value-changed",{value:this.value})):!this.selector.device?.multiple&&Array.isArray(this.value)&&(this.value=this.value[0],(0,n.r)(this,"value-changed",{value:this.value})))}updated(e){super.updated(e),e.has("selector")&&this._hasIntegration(this.selector)&&!this._entitySources&&(0,h.c)(this.hass).then((e=>{this._entitySources=e})),!this._configEntries&&this._hasIntegration(this.selector)&&(this._configEntries=[],(0,p.VN)(this.hass).then((e=>{this._configEntries=e})))}render(){return this._hasIntegration(this.selector)&&!this._entitySources?o.s6:this.selector.device?.multiple?o.qy`
      ${this.label?o.qy`<label>${this.label}</label>`:""}
      <ha-devices-picker
        .hass=${this.hass}
        .value=${this.value}
        .helper=${this.helper}
        .deviceFilter=${this._filterDevices}
        .entityFilter=${this.selector.device?.entity?this._filterEntities:void 0}
        .disabled=${this.disabled}
        .required=${this.required}
      ></ha-devices-picker>
    `:o.qy`
        <ha-device-picker
          .hass=${this.hass}
          .value=${this.value}
          .label=${this.label}
          .helper=${this.helper}
          .deviceFilter=${this._filterDevices}
          .entityFilter=${this.selector.device?.entity?this._filterEntities:void 0}
          .placeholder=${this.placeholder}
          .disabled=${this.disabled}
          .required=${this.required}
          allow-custom-entity
        ></ha-device-picker>
      `}constructor(...e){super(...e),this.disabled=!1,this.required=!0,this._deviceIntegrationLookup=(0,c.A)(l.fk),this._filterDevices=e=>{if(!this.selector.device?.filter)return!0;const t=this._entitySources?this._deviceIntegrationLookup(this._entitySources,Object.values(this.hass.entities),Object.values(this.hass.devices),this._configEntries):void 0;return(0,d.e)(this.selector.device.filter).some((i=>(0,u.vX)(i,e,t)))},this._filterEntities=e=>(0,d.e)(this.selector.device.entity).some((t=>(0,u.Ru)(t,e,this._entitySources)))}}(0,r.__decorate)([(0,a.MZ)({attribute:!1})],b.prototype,"hass",void 0),(0,r.__decorate)([(0,a.MZ)({attribute:!1})],b.prototype,"selector",void 0),(0,r.__decorate)([(0,a.wk)()],b.prototype,"_entitySources",void 0),(0,r.__decorate)([(0,a.wk)()],b.prototype,"_configEntries",void 0),(0,r.__decorate)([(0,a.MZ)()],b.prototype,"value",void 0),(0,r.__decorate)([(0,a.MZ)()],b.prototype,"label",void 0),(0,r.__decorate)([(0,a.MZ)()],b.prototype,"helper",void 0),(0,r.__decorate)([(0,a.MZ)()],b.prototype,"placeholder",void 0),(0,r.__decorate)([(0,a.MZ)({type:Boolean})],b.prototype,"disabled",void 0),(0,r.__decorate)([(0,a.MZ)({type:Boolean})],b.prototype,"required",void 0),b=(0,r.__decorate)([(0,a.EM)("ha-selector-device")],b),s()}catch(b){s(b)}}))},28441:function(e,t,i){i.d(t,{c:()=>o});const s=async(e,t,i,r,o,...a)=>{const c=o,d=c[e],n=d=>r&&r(o,d.result)!==d.cacheKey?(c[e]=void 0,s(e,t,i,r,o,...a)):d.result;if(d)return d instanceof Promise?d.then(n):n(d);const l=i(o,...a);return c[e]=l,l.then((i=>{c[e]={result:i,cacheKey:r?.(o,i)},setTimeout((()=>{c[e]=void 0}),t)}),(()=>{c[e]=void 0})),l},r=e=>e.callWS({type:"entity/source"}),o=e=>s("_entitySources",3e4,r,(e=>Object.keys(e.states).length),e)},76681:function(e,t,i){i.d(t,{MR:()=>s,a_:()=>r,bg:()=>o});const s=e=>`https://brands.home-assistant.io/${e.brand?"brands/":""}${e.useFallback?"_/":""}${e.domain}/${e.darkOptimized?"dark_":""}${e.type}.png`,r=e=>e.split("/")[4],o=e=>e.startsWith("https://brands.home-assistant.io/")}};
//# sourceMappingURL=2816.d98ac974d1fa79d7.js.map
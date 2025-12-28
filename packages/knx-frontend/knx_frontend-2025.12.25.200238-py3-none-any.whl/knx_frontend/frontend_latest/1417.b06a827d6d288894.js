export const __webpack_id__="1417";export const __webpack_ids__=["1417"];export const __webpack_modules__={45134:function(e,t,i){i.a(e,(async function(e,t){try{var s=i(62826),r=i(96196),a=i(77845),o=i(92542),c=i(10085),d=i(53907),h=e([d]);d=(h.then?(await h)():h)[0];class n extends((0,c.E)(r.WF)){render(){if(!this.hass)return r.s6;const e=this._currentAreas;return r.qy`
      ${e.map((e=>r.qy`
          <div>
            <ha-area-picker
              .curValue=${e}
              .noAdd=${this.noAdd}
              .hass=${this.hass}
              .value=${e}
              .label=${this.pickedAreaLabel}
              .includeDomains=${this.includeDomains}
              .excludeDomains=${this.excludeDomains}
              .includeDeviceClasses=${this.includeDeviceClasses}
              .deviceFilter=${this.deviceFilter}
              .entityFilter=${this.entityFilter}
              .disabled=${this.disabled}
              @value-changed=${this._areaChanged}
            ></ha-area-picker>
          </div>
        `))}
      <div>
        <ha-area-picker
          .noAdd=${this.noAdd}
          .hass=${this.hass}
          .label=${this.pickAreaLabel}
          .helper=${this.helper}
          .includeDomains=${this.includeDomains}
          .excludeDomains=${this.excludeDomains}
          .includeDeviceClasses=${this.includeDeviceClasses}
          .deviceFilter=${this.deviceFilter}
          .entityFilter=${this.entityFilter}
          .disabled=${this.disabled}
          .placeholder=${this.placeholder}
          .required=${this.required&&!e.length}
          @value-changed=${this._addArea}
          .excludeAreas=${e}
        ></ha-area-picker>
      </div>
    `}get _currentAreas(){return this.value||[]}async _updateAreas(e){this.value=e,(0,o.r)(this,"value-changed",{value:e})}_areaChanged(e){e.stopPropagation();const t=e.currentTarget.curValue,i=e.detail.value;if(i===t)return;const s=this._currentAreas;i&&!s.includes(i)?this._updateAreas(s.map((e=>e===t?i:e))):this._updateAreas(s.filter((e=>e!==t)))}_addArea(e){e.stopPropagation();const t=e.detail.value;if(!t)return;e.currentTarget.value="";const i=this._currentAreas;i.includes(t)||this._updateAreas([...i,t])}constructor(...e){super(...e),this.noAdd=!1,this.disabled=!1,this.required=!1}}n.styles=r.AH`
    div {
      margin-top: 8px;
    }
  `,(0,s.__decorate)([(0,a.MZ)({attribute:!1})],n.prototype,"hass",void 0),(0,s.__decorate)([(0,a.MZ)()],n.prototype,"label",void 0),(0,s.__decorate)([(0,a.MZ)({type:Array})],n.prototype,"value",void 0),(0,s.__decorate)([(0,a.MZ)()],n.prototype,"helper",void 0),(0,s.__decorate)([(0,a.MZ)()],n.prototype,"placeholder",void 0),(0,s.__decorate)([(0,a.MZ)({type:Boolean,attribute:"no-add"})],n.prototype,"noAdd",void 0),(0,s.__decorate)([(0,a.MZ)({type:Array,attribute:"include-domains"})],n.prototype,"includeDomains",void 0),(0,s.__decorate)([(0,a.MZ)({type:Array,attribute:"exclude-domains"})],n.prototype,"excludeDomains",void 0),(0,s.__decorate)([(0,a.MZ)({type:Array,attribute:"include-device-classes"})],n.prototype,"includeDeviceClasses",void 0),(0,s.__decorate)([(0,a.MZ)({attribute:!1})],n.prototype,"deviceFilter",void 0),(0,s.__decorate)([(0,a.MZ)({attribute:!1})],n.prototype,"entityFilter",void 0),(0,s.__decorate)([(0,a.MZ)({attribute:"picked-area-label"})],n.prototype,"pickedAreaLabel",void 0),(0,s.__decorate)([(0,a.MZ)({attribute:"pick-area-label"})],n.prototype,"pickAreaLabel",void 0),(0,s.__decorate)([(0,a.MZ)({type:Boolean})],n.prototype,"disabled",void 0),(0,s.__decorate)([(0,a.MZ)({type:Boolean})],n.prototype,"required",void 0),n=(0,s.__decorate)([(0,a.EM)("ha-areas-picker")],n),t()}catch(n){t(n)}}))},87888:function(e,t,i){i.a(e,(async function(e,s){try{i.r(t),i.d(t,{HaAreaSelector:()=>b});var r=i(62826),a=i(96196),o=i(77845),c=i(22786),d=i(55376),h=i(1491),n=i(92542),l=i(28441),u=i(3950),p=i(82694),_=i(53907),v=i(45134),y=e([_,v]);[_,v]=y.then?(await y)():y;class b extends a.WF{_hasIntegration(e){return e.area?.entity&&(0,d.e)(e.area.entity).some((e=>e.integration))||e.area?.device&&(0,d.e)(e.area.device).some((e=>e.integration))}willUpdate(e){e.get("selector")&&void 0!==this.value&&(this.selector.area?.multiple&&!Array.isArray(this.value)?(this.value=[this.value],(0,n.r)(this,"value-changed",{value:this.value})):!this.selector.area?.multiple&&Array.isArray(this.value)&&(this.value=this.value[0],(0,n.r)(this,"value-changed",{value:this.value})))}updated(e){e.has("selector")&&this._hasIntegration(this.selector)&&!this._entitySources&&(0,l.c)(this.hass).then((e=>{this._entitySources=e})),!this._configEntries&&this._hasIntegration(this.selector)&&(this._configEntries=[],(0,u.VN)(this.hass).then((e=>{this._configEntries=e})))}render(){return this._hasIntegration(this.selector)&&!this._entitySources?a.s6:this.selector.area?.multiple?a.qy`
      <ha-areas-picker
        .hass=${this.hass}
        .value=${this.value}
        .helper=${this.helper}
        .pickAreaLabel=${this.label}
        no-add
        .deviceFilter=${this.selector.area?.device?this._filterDevices:void 0}
        .entityFilter=${this.selector.area?.entity?this._filterEntities:void 0}
        .disabled=${this.disabled}
        .required=${this.required}
      ></ha-areas-picker>
    `:a.qy`
        <ha-area-picker
          .hass=${this.hass}
          .value=${this.value}
          .label=${this.label}
          .helper=${this.helper}
          no-add
          .deviceFilter=${this.selector.area?.device?this._filterDevices:void 0}
          .entityFilter=${this.selector.area?.entity?this._filterEntities:void 0}
          .disabled=${this.disabled}
          .required=${this.required}
        ></ha-area-picker>
      `}constructor(...e){super(...e),this.disabled=!1,this.required=!0,this._deviceIntegrationLookup=(0,c.A)(h.fk),this._filterEntities=e=>!this.selector.area?.entity||(0,d.e)(this.selector.area.entity).some((t=>(0,p.Ru)(t,e,this._entitySources))),this._filterDevices=e=>{if(!this.selector.area?.device)return!0;const t=this._entitySources?this._deviceIntegrationLookup(this._entitySources,Object.values(this.hass.entities),Object.values(this.hass.devices),this._configEntries):void 0;return(0,d.e)(this.selector.area.device).some((i=>(0,p.vX)(i,e,t)))}}}(0,r.__decorate)([(0,o.MZ)({attribute:!1})],b.prototype,"hass",void 0),(0,r.__decorate)([(0,o.MZ)({attribute:!1})],b.prototype,"selector",void 0),(0,r.__decorate)([(0,o.MZ)()],b.prototype,"value",void 0),(0,r.__decorate)([(0,o.MZ)()],b.prototype,"label",void 0),(0,r.__decorate)([(0,o.MZ)()],b.prototype,"helper",void 0),(0,r.__decorate)([(0,o.MZ)({type:Boolean})],b.prototype,"disabled",void 0),(0,r.__decorate)([(0,o.MZ)({type:Boolean})],b.prototype,"required",void 0),(0,r.__decorate)([(0,o.wk)()],b.prototype,"_entitySources",void 0),(0,r.__decorate)([(0,o.wk)()],b.prototype,"_configEntries",void 0),b=(0,r.__decorate)([(0,o.EM)("ha-selector-area")],b),s()}catch(b){s(b)}}))},28441:function(e,t,i){i.d(t,{c:()=>a});const s=async(e,t,i,r,a,...o)=>{const c=a,d=c[e],h=d=>r&&r(a,d.result)!==d.cacheKey?(c[e]=void 0,s(e,t,i,r,a,...o)):d.result;if(d)return d instanceof Promise?d.then(h):h(d);const n=i(a,...o);return c[e]=n,n.then((i=>{c[e]={result:i,cacheKey:r?.(a,i)},setTimeout((()=>{c[e]=void 0}),t)}),(()=>{c[e]=void 0})),n},r=e=>e.callWS({type:"entity/source"}),a=e=>s("_entitySources",3e4,r,(e=>Object.keys(e.states).length),e)},10085:function(e,t,i){i.d(t,{E:()=>a});var s=i(62826),r=i(77845);const a=e=>{class t extends e{connectedCallback(){super.connectedCallback(),this._checkSubscribed()}disconnectedCallback(){if(super.disconnectedCallback(),this.__unsubs){for(;this.__unsubs.length;){const e=this.__unsubs.pop();e instanceof Promise?e.then((e=>e())):e()}this.__unsubs=void 0}}updated(e){if(super.updated(e),e.has("hass"))this._checkSubscribed();else if(this.hassSubscribeRequiredHostProps)for(const t of e.keys())if(this.hassSubscribeRequiredHostProps.includes(t))return void this._checkSubscribed()}hassSubscribe(){return[]}_checkSubscribed(){void 0===this.__unsubs&&this.isConnected&&void 0!==this.hass&&!this.hassSubscribeRequiredHostProps?.some((e=>void 0===this[e]))&&(this.__unsubs=this.hassSubscribe())}}return(0,s.__decorate)([(0,r.MZ)({attribute:!1})],t.prototype,"hass",void 0),t}}};
//# sourceMappingURL=1417.b06a827d6d288894.js.map
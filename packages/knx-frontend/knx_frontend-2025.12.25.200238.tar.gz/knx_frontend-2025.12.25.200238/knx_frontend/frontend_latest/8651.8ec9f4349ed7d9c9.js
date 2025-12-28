/*! For license information please see 8651.8ec9f4349ed7d9c9.js.LICENSE.txt */
export const __webpack_id__="8651";export const __webpack_ids__=["8651"];export const __webpack_modules__={32637:function(e,t,i){i.a(e,(async function(e,t){try{var s=i(62826),r=i(96196),n=i(77845),o=i(22786),a=i(92542),c=i(45996),l=(i(63801),i(82965)),d=e([l]);l=(d.then?(await d)():d)[0];const h="M21 11H3V9H21V11M21 13H3V15H21V13Z";class u extends r.WF{render(){if(!this.hass)return r.s6;const e=this._currentEntities;return r.qy`
      ${this.label?r.qy`<label>${this.label}</label>`:r.s6}
      <ha-sortable
        .disabled=${!this.reorder||this.disabled}
        handle-selector=".entity-handle"
        @item-moved=${this._entityMoved}
      >
        <div class="list">
          ${e.map((e=>r.qy`
              <div class="entity">
                <ha-entity-picker
                  allow-custom-entity
                  .curValue=${e}
                  .hass=${this.hass}
                  .includeDomains=${this.includeDomains}
                  .excludeDomains=${this.excludeDomains}
                  .includeEntities=${this.includeEntities}
                  .excludeEntities=${this.excludeEntities}
                  .includeDeviceClasses=${this.includeDeviceClasses}
                  .includeUnitOfMeasurement=${this.includeUnitOfMeasurement}
                  .entityFilter=${this.entityFilter}
                  .value=${e}
                  .disabled=${this.disabled}
                  .createDomains=${this.createDomains}
                  @value-changed=${this._entityChanged}
                ></ha-entity-picker>
                ${this.reorder?r.qy`
                      <ha-svg-icon
                        class="entity-handle"
                        .path=${h}
                      ></ha-svg-icon>
                    `:r.s6}
              </div>
            `))}
        </div>
      </ha-sortable>
      <div>
        <ha-entity-picker
          allow-custom-entity
          .hass=${this.hass}
          .includeDomains=${this.includeDomains}
          .excludeDomains=${this.excludeDomains}
          .includeEntities=${this.includeEntities}
          .excludeEntities=${this._excludeEntities(this.value,this.excludeEntities)}
          .includeDeviceClasses=${this.includeDeviceClasses}
          .includeUnitOfMeasurement=${this.includeUnitOfMeasurement}
          .entityFilter=${this.entityFilter}
          .placeholder=${this.placeholder}
          .helper=${this.helper}
          .disabled=${this.disabled}
          .createDomains=${this.createDomains}
          .required=${this.required&&!e.length}
          @value-changed=${this._addEntity}
          .addButton=${e.length>0}
        ></ha-entity-picker>
      </div>
    `}_entityMoved(e){e.stopPropagation();const{oldIndex:t,newIndex:i}=e.detail,s=this._currentEntities,r=s[t],n=[...s];n.splice(t,1),n.splice(i,0,r),this._updateEntities(n)}get _currentEntities(){return this.value||[]}async _updateEntities(e){this.value=e,(0,a.r)(this,"value-changed",{value:e})}_entityChanged(e){e.stopPropagation();const t=e.currentTarget.curValue,i=e.detail.value;if(i===t||void 0!==i&&!(0,c.n)(i))return;const s=this._currentEntities;i&&!s.includes(i)?this._updateEntities(s.map((e=>e===t?i:e))):this._updateEntities(s.filter((e=>e!==t)))}async _addEntity(e){e.stopPropagation();const t=e.detail.value;if(!t)return;if(e.currentTarget.value="",!t)return;const i=this._currentEntities;i.includes(t)||this._updateEntities([...i,t])}constructor(...e){super(...e),this.disabled=!1,this.required=!1,this.reorder=!1,this._excludeEntities=(0,o.A)(((e,t)=>void 0===e?t:[...t||[],...e]))}}u.styles=r.AH`
    div {
      margin-top: 8px;
    }
    label {
      display: block;
      margin: 0 0 8px;
    }
    .entity {
      display: flex;
      flex-direction: row;
      align-items: center;
    }
    .entity ha-entity-picker {
      flex: 1;
    }
    .entity-handle {
      padding: 8px;
      cursor: move; /* fallback if grab cursor is unsupported */
      cursor: grab;
    }
  `,(0,s.__decorate)([(0,n.MZ)({attribute:!1})],u.prototype,"hass",void 0),(0,s.__decorate)([(0,n.MZ)({type:Array})],u.prototype,"value",void 0),(0,s.__decorate)([(0,n.MZ)({type:Boolean})],u.prototype,"disabled",void 0),(0,s.__decorate)([(0,n.MZ)({type:Boolean})],u.prototype,"required",void 0),(0,s.__decorate)([(0,n.MZ)()],u.prototype,"label",void 0),(0,s.__decorate)([(0,n.MZ)()],u.prototype,"placeholder",void 0),(0,s.__decorate)([(0,n.MZ)()],u.prototype,"helper",void 0),(0,s.__decorate)([(0,n.MZ)({type:Array,attribute:"include-domains"})],u.prototype,"includeDomains",void 0),(0,s.__decorate)([(0,n.MZ)({type:Array,attribute:"exclude-domains"})],u.prototype,"excludeDomains",void 0),(0,s.__decorate)([(0,n.MZ)({type:Array,attribute:"include-device-classes"})],u.prototype,"includeDeviceClasses",void 0),(0,s.__decorate)([(0,n.MZ)({type:Array,attribute:"include-unit-of-measurement"})],u.prototype,"includeUnitOfMeasurement",void 0),(0,s.__decorate)([(0,n.MZ)({type:Array,attribute:"include-entities"})],u.prototype,"includeEntities",void 0),(0,s.__decorate)([(0,n.MZ)({type:Array,attribute:"exclude-entities"})],u.prototype,"excludeEntities",void 0),(0,s.__decorate)([(0,n.MZ)({attribute:!1})],u.prototype,"entityFilter",void 0),(0,s.__decorate)([(0,n.MZ)({attribute:!1,type:Array})],u.prototype,"createDomains",void 0),(0,s.__decorate)([(0,n.MZ)({type:Boolean})],u.prototype,"reorder",void 0),u=(0,s.__decorate)([(0,n.EM)("ha-entities-picker")],u),t()}catch(h){t(h)}}))},25394:function(e,t,i){i.a(e,(async function(e,s){try{i.r(t),i.d(t,{HaEntitySelector:()=>_});var r=i(62826),n=i(96196),o=i(77845),a=i(55376),c=i(92542),l=i(28441),d=i(82694),h=i(32637),u=i(82965),p=e([h,u]);[h,u]=p.then?(await p)():p;class _ extends n.WF{_hasIntegration(e){return e.entity?.filter&&(0,a.e)(e.entity.filter).some((e=>e.integration))}willUpdate(e){e.get("selector")&&void 0!==this.value&&(this.selector.entity?.multiple&&!Array.isArray(this.value)?(this.value=[this.value],(0,c.r)(this,"value-changed",{value:this.value})):!this.selector.entity?.multiple&&Array.isArray(this.value)&&(this.value=this.value[0],(0,c.r)(this,"value-changed",{value:this.value})))}render(){return this._hasIntegration(this.selector)&&!this._entitySources?n.s6:this.selector.entity?.multiple?n.qy`
      <ha-entities-picker
        .hass=${this.hass}
        .value=${this.value}
        .label=${this.label}
        .helper=${this.helper}
        .includeEntities=${this.selector.entity.include_entities}
        .excludeEntities=${this.selector.entity.exclude_entities}
        .reorder=${this.selector.entity.reorder??!1}
        .entityFilter=${this._filterEntities}
        .createDomains=${this._createDomains}
        .placeholder=${this.placeholder}
        .disabled=${this.disabled}
        .required=${this.required}
      ></ha-entities-picker>
    `:n.qy`<ha-entity-picker
        .hass=${this.hass}
        .value=${this.value}
        .label=${this.label}
        .helper=${this.helper}
        .includeEntities=${this.selector.entity?.include_entities}
        .excludeEntities=${this.selector.entity?.exclude_entities}
        .entityFilter=${this._filterEntities}
        .createDomains=${this._createDomains}
        .placeholder=${this.placeholder}
        .disabled=${this.disabled}
        .required=${this.required}
        allow-custom-entity
      ></ha-entity-picker>`}updated(e){super.updated(e),e.has("selector")&&this._hasIntegration(this.selector)&&!this._entitySources&&(0,l.c)(this.hass).then((e=>{this._entitySources=e})),e.has("selector")&&(this._createDomains=(0,d.Lo)(this.selector))}constructor(...e){super(...e),this.disabled=!1,this.required=!0,this._filterEntities=e=>!this.selector?.entity?.filter||(0,a.e)(this.selector.entity.filter).some((t=>(0,d.Ru)(t,e,this._entitySources)))}}(0,r.__decorate)([(0,o.MZ)({attribute:!1})],_.prototype,"hass",void 0),(0,r.__decorate)([(0,o.MZ)({attribute:!1})],_.prototype,"selector",void 0),(0,r.__decorate)([(0,o.wk)()],_.prototype,"_entitySources",void 0),(0,r.__decorate)([(0,o.MZ)()],_.prototype,"value",void 0),(0,r.__decorate)([(0,o.MZ)()],_.prototype,"label",void 0),(0,r.__decorate)([(0,o.MZ)()],_.prototype,"helper",void 0),(0,r.__decorate)([(0,o.MZ)()],_.prototype,"placeholder",void 0),(0,r.__decorate)([(0,o.MZ)({type:Boolean})],_.prototype,"disabled",void 0),(0,r.__decorate)([(0,o.MZ)({type:Boolean})],_.prototype,"required",void 0),(0,r.__decorate)([(0,o.wk)()],_.prototype,"_createDomains",void 0),_=(0,r.__decorate)([(0,o.EM)("ha-selector-entity")],_),s()}catch(_){s(_)}}))},28441:function(e,t,i){i.d(t,{c:()=>n});const s=async(e,t,i,r,n,...o)=>{const a=n,c=a[e],l=c=>r&&r(n,c.result)!==c.cacheKey?(a[e]=void 0,s(e,t,i,r,n,...o)):c.result;if(c)return c instanceof Promise?c.then(l):l(c);const d=i(n,...o);return a[e]=d,d.then((i=>{a[e]={result:i,cacheKey:r?.(n,i)},setTimeout((()=>{a[e]=void 0}),t)}),(()=>{a[e]=void 0})),d},r=e=>e.callWS({type:"entity/source"}),n=e=>s("_entitySources",3e4,r,(e=>Object.keys(e.states).length),e)},70570:function(e,t,i){i.d(t,{N:()=>n});const s=e=>{let t=[];function i(i,s){e=s?i:Object.assign(Object.assign({},e),i);let r=t;for(let t=0;t<r.length;t++)r[t](e)}return{get state(){return e},action(t){function s(e){i(e,!1)}return function(){let i=[e];for(let e=0;e<arguments.length;e++)i.push(arguments[e]);let r=t.apply(this,i);if(null!=r)return r instanceof Promise?r.then(s):s(r)}},setState:i,clearState(){e=void 0},subscribe(e){return t.push(e),()=>{!function(e){let i=[];for(let s=0;s<t.length;s++)t[s]===e?e=null:i.push(t[s]);t=i}(e)}}}},r=(e,t,i,r,n={unsubGrace:!0})=>{if(e[t])return e[t];let o,a,c=0,l=s();const d=()=>{if(!i)throw new Error("Collection does not support refresh");return i(e).then((e=>l.setState(e,!0)))},h=()=>d().catch((t=>{if(e.connected)throw t})),u=()=>{a=void 0,o&&o.then((e=>{e()})),l.clearState(),e.removeEventListener("ready",d),e.removeEventListener("disconnected",p)},p=()=>{a&&(clearTimeout(a),u())};return e[t]={get state(){return l.state},refresh:d,subscribe(t){c++,1===c&&(()=>{if(void 0!==a)return clearTimeout(a),void(a=void 0);r&&(o=r(e,l)),i&&(e.addEventListener("ready",h),h()),e.addEventListener("disconnected",p)})();const s=l.subscribe(t);return void 0!==l.state&&setTimeout((()=>t(l.state)),0),()=>{s(),c--,c||(n.unsubGrace?a=setTimeout(u,5e3):u())}}},e[t]},n=(e,t,i,s,n)=>r(s,e,t,i).subscribe(n)},3890:function(e,t,i){i.d(t,{T:()=>u});var s=i(5055),r=i(63937),n=i(37540);class o{disconnect(){this.G=void 0}reconnect(e){this.G=e}deref(){return this.G}constructor(e){this.G=e}}class a{get(){return this.Y}pause(){this.Y??=new Promise((e=>this.Z=e))}resume(){this.Z?.(),this.Y=this.Z=void 0}constructor(){this.Y=void 0,this.Z=void 0}}var c=i(42017);const l=e=>!(0,r.sO)(e)&&"function"==typeof e.then,d=1073741823;class h extends n.Kq{render(...e){return e.find((e=>!l(e)))??s.c0}update(e,t){const i=this._$Cbt;let r=i.length;this._$Cbt=t;const n=this._$CK,o=this._$CX;this.isConnected||this.disconnected();for(let s=0;s<t.length&&!(s>this._$Cwt);s++){const e=t[s];if(!l(e))return this._$Cwt=s,e;s<r&&e===i[s]||(this._$Cwt=d,r=0,Promise.resolve(e).then((async t=>{for(;o.get();)await o.get();const i=n.deref();if(void 0!==i){const s=i._$Cbt.indexOf(e);s>-1&&s<i._$Cwt&&(i._$Cwt=s,i.setValue(t))}})))}return s.c0}disconnected(){this._$CK.disconnect(),this._$CX.pause()}reconnected(){this._$CK.reconnect(this),this._$CX.resume()}constructor(){super(...arguments),this._$Cwt=d,this._$Cbt=[],this._$CK=new o(this),this._$CX=new a}}const u=(0,c.u$)(h)}};
//# sourceMappingURL=8651.8ec9f4349ed7d9c9.js.map
/*! For license information please see 3012.2e9005ad1b523dc3.js.LICENSE.txt */
export const __webpack_id__="3012";export const __webpack_ids__=["3012"];export const __webpack_modules__={87328:function(t,e,i){i.d(e,{aH:()=>r});var s=i(16727),a=i(91889);const o=[" ",": "," - "],n=t=>t.toLowerCase()!==t,r=(t,e,i)=>{const s=e[t.entity_id];return s?c(s,i):(0,a.u)(t)},c=(t,e,i)=>{const r=t.name||("original_name"in t&&null!=t.original_name?String(t.original_name):void 0),c=t.device_id?e[t.device_id]:void 0;if(!c)return r||(i?(0,a.u)(i):void 0);const l=(0,s.xn)(c);return l!==r?l&&r&&((t,e)=>{const i=t.toLowerCase(),s=e.toLowerCase();for(const a of o){const e=`${s}${a}`;if(i.startsWith(e)){const i=t.substring(e.length);if(i.length)return n(i.substr(0,i.indexOf(" ")))?i:i[0].toUpperCase()+i.slice(1)}}})(r,l)||r:void 0}},79384:function(t,e,i){i.d(e,{Cf:()=>c});var s=i(56403),a=i(16727),o=i(87328),n=i(47644),r=i(87400);const c=(t,e,i,c,l,d)=>{const{device:h,area:u,floor:p}=(0,r.l)(t,i,c,l,d);return e.map((e=>{switch(e.type){case"entity":return(0,o.aH)(t,i,c);case"device":return h?(0,a.xn)(h):void 0;case"area":return u?(0,s.A)(u):void 0;case"floor":return p?(0,n.X)(p):void 0;case"text":return e.text;default:return""}}))}},87400:function(t,e,i){i.d(e,{l:()=>s});const s=(t,e,i,s,o)=>{const n=e[t.entity_id];return n?a(n,e,i,s,o):{entity:null,device:null,area:null,floor:null}},a=(t,e,i,s,a)=>{const o=e[t.entity_id],n=t?.device_id,r=n?i[n]:void 0,c=t?.area_id||r?.area_id,l=c?s[c]:void 0,d=l?.floor_id;return{entity:o,device:r||null,area:l||null,floor:(d?a[d]:void 0)||null}}},60042:function(t,e,i){i.a(t,(async function(t,e){try{var s=i(62826),a=i(96196),o=i(77845),n=i(22786),r=i(55376),c=i(92542),l=i(79384),d=i(91889),h=i(79599),u=i(84125),p=i(37157),_=i(62001),y=(i(94343),i(96943)),v=(i(60733),i(60961),i(91720)),$=t([y,v]);[y,v]=$.then?(await $)():$;const b="M16,11.78L20.24,4.45L21.97,5.45L16.74,14.5L10.23,10.75L5.46,19H22V21H2V3H4V17.54L9.5,8L16,11.78Z",f="M15.07,11.25L14.17,12.17C13.45,12.89 13,13.5 13,15H11V14.5C11,13.39 11.45,12.39 12.17,11.67L13.41,10.41C13.78,10.05 14,9.55 14,9C14,7.89 13.1,7 12,7A2,2 0 0,0 10,9H8A4,4 0 0,1 12,5A4,4 0 0,1 16,9C16,9.88 15.64,10.67 15.07,11.25M13,19H11V17H13M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12C22,6.47 17.5,2 12,2Z",m="M11,13.5V21.5H3V13.5H11M12,2L17.5,11H6.5L12,2M17.5,13C20,13 22,15 22,17.5C22,20 20,22 17.5,22C15,22 13,20 13,17.5C13,15 15,13 17.5,13Z",g=["entity","external","no_state"],C="___missing-entity___";class M extends a.WF{willUpdate(t){(!this.hasUpdated&&!this.statisticIds||t.has("statisticTypes"))&&this._getStatisticIds()}async _getStatisticIds(){this.statisticIds=await(0,p.p3)(this.hass,this.statisticTypes)}_getAdditionalItems(){return[{id:C,primary:this.hass.localize("ui.components.statistic-picker.missing_entity"),icon_path:f}]}_computeItem(t){const e=this.hass.states[t];if(e){const[i,s,a]=(0,l.Cf)(e,[{type:"entity"},{type:"device"},{type:"area"}],this.hass.entities,this.hass.devices,this.hass.areas,this.hass.floors),o=(0,h.qC)(this.hass),n=i||s||t,r=[a,i?s:void 0].filter(Boolean).join(o?" ◂ ":" ▸ "),c=(0,d.u)(e);return{id:t,statistic_id:t,primary:n,secondary:r,stateObj:e,type:"entity",sorting_label:[`${g.indexOf("entity")}`,s,i].join("_"),search_labels:[i,s,a,c,t].filter(Boolean)}}const i=this.statisticIds?this._statisticMetaData(t,this.statisticIds):void 0;if(i){if("external"===(t.includes(":")&&!t.includes(".")?"external":"no_state")){const e=`${g.indexOf("external")}`,s=(0,p.$O)(this.hass,t,i),a=t.split(":")[0],o=(0,u.p$)(this.hass.localize,a);return{id:t,statistic_id:t,primary:s,secondary:o,type:"external",sorting_label:[e,s].join("_"),search_labels:[s,o,t],icon_path:b}}}const s=`${g.indexOf("external")}`,a=(0,p.$O)(this.hass,t,i);return{id:t,primary:a,secondary:this.hass.localize("ui.components.statistic-picker.no_state"),type:"no_state",sorting_label:[s,a].join("_"),search_labels:[a,t],icon_path:m}}render(){const t=this.placeholder??this.hass.localize("ui.components.statistic-picker.placeholder");return a.qy`
      <ha-generic-picker
        .hass=${this.hass}
        .autofocus=${this.autofocus}
        .allowCustomValue=${this.allowCustomEntity}
        .label=${this.label}
        .notFoundLabel=${this._notFoundLabel}
        .emptyLabel=${this.hass.localize("ui.components.statistic-picker.no_statistics")}
        .placeholder=${t}
        .value=${this.value}
        .rowRenderer=${this._rowRenderer}
        .getItems=${this._getItems}
        .getAdditionalItems=${this._getAdditionalItems}
        .hideClearIcon=${this.hideClearIcon}
        .searchFn=${this._searchFn}
        .valueRenderer=${this._valueRenderer}
        .helper=${this.helper}
        @value-changed=${this._valueChanged}
      >
      </ha-generic-picker>
    `}_valueChanged(t){t.stopPropagation();const e=t.detail.value;e!==C?(this.value=e,(0,c.r)(this,"value-changed",{value:e})):window.open((0,_.o)(this.hass,this.helpMissingEntityUrl),"_blank")}async open(){await this.updateComplete,await(this._picker?.open())}constructor(...t){super(...t),this.autofocus=!1,this.disabled=!1,this.required=!1,this.helpMissingEntityUrl="/more-info/statistics/",this.entitiesOnly=!1,this.hideClearIcon=!1,this._getItems=()=>this._getStatisticsItems(this.hass,this.statisticIds,this.includeStatisticsUnitOfMeasurement,this.includeUnitClass,this.includeDeviceClass,this.entitiesOnly,this.excludeStatistics,this.value),this._getStatisticsItems=(0,n.A)(((t,e,i,s,a,o,n,c)=>{if(!e)return[];if(i){const t=(0,r.e)(i);e=e.filter((e=>t.includes(e.statistics_unit_of_measurement)))}if(s){const t=(0,r.e)(s);e=e.filter((e=>t.includes(e.unit_class)))}if(a){const t=(0,r.e)(a);e=e.filter((e=>{const i=this.hass.states[e.statistic_id];return!i||t.includes(i.attributes.device_class||"")}))}const _=(0,h.qC)(t),y=[];return e.forEach((e=>{if(n&&e.statistic_id!==c&&n.includes(e.statistic_id))return;const i=this.hass.states[e.statistic_id];if(!i){if(!o){const t=e.statistic_id,i=(0,p.$O)(this.hass,e.statistic_id,e),s=e.statistic_id.includes(":")&&!e.statistic_id.includes(".")?"external":"no_state",a=`${g.indexOf(s)}`;if("no_state"===s)y.push({id:t,primary:i,secondary:this.hass.localize("ui.components.statistic-picker.no_state"),type:s,sorting_label:[a,i].join("_"),search_labels:[i,t],icon_path:m});else if("external"===s){const e=t.split(":")[0],o=(0,u.p$)(this.hass.localize,e);y.push({id:t,statistic_id:t,primary:i,secondary:o,type:s,sorting_label:[a,i].join("_"),search_labels:[i,o,t],icon_path:b})}}return}const s=e.statistic_id,a=(0,d.u)(i),[r,h,v]=(0,l.Cf)(i,[{type:"entity"},{type:"device"},{type:"area"}],t.entities,t.devices,t.areas,t.floors),$=r||h||s,f=[v,r?h:void 0].filter(Boolean).join(_?" ◂ ":" ▸ "),C=`${g.indexOf("entity")}`;y.push({id:s,statistic_id:s,primary:$,secondary:f,stateObj:i,type:"entity",sorting_label:[C,h,r].join("_"),search_labels:[r,h,v,a,s].filter(Boolean)})})),y})),this._statisticMetaData=(0,n.A)(((t,e)=>{if(e)return e.find((e=>e.statistic_id===t))})),this._valueRenderer=t=>{const e=t,i=this._computeItem(e);return a.qy`
      ${i.stateObj?a.qy`
            <state-badge
              .hass=${this.hass}
              .stateObj=${i.stateObj}
              slot="start"
            ></state-badge>
          `:i.icon_path?a.qy`
              <ha-svg-icon slot="start" .path=${i.icon_path}></ha-svg-icon>
            `:a.s6}
      <span slot="headline">${i.primary}</span>
      ${i.secondary?a.qy`<span slot="supporting-text">${i.secondary}</span>`:a.s6}
    `},this._rowRenderer=(t,{index:e})=>{const i=this.hass.userData?.showEntityIdPicker;return a.qy`
      <ha-combo-box-item type="button" compact .borderTop=${0!==e}>
        ${t.icon_path?a.qy`
              <ha-svg-icon
                style="margin: 0 4px"
                slot="start"
                .path=${t.icon_path}
              ></ha-svg-icon>
            `:t.stateObj?a.qy`
                <state-badge
                  slot="start"
                  .stateObj=${t.stateObj}
                  .hass=${this.hass}
                ></state-badge>
              `:a.s6}
        <span slot="headline">${t.primary} </span>
        ${t.secondary?a.qy`<span slot="supporting-text">${t.secondary}</span>`:a.s6}
        ${t.statistic_id&&i?a.qy`<span slot="supporting-text" class="code">
              ${t.statistic_id}
            </span>`:a.s6}
      </ha-combo-box-item>
    `},this._searchFn=(t,e)=>{const i=e.findIndex((e=>e.stateObj?.entity_id===t||e.statistic_id===t));if(-1===i)return e;const[s]=e.splice(i,1);return e.unshift(s),e},this._notFoundLabel=t=>this.hass.localize("ui.components.statistic-picker.no_match",{term:a.qy`<b>‘${t}’</b>`})}}(0,s.__decorate)([(0,o.MZ)({attribute:!1})],M.prototype,"hass",void 0),(0,s.__decorate)([(0,o.MZ)({type:Boolean})],M.prototype,"autofocus",void 0),(0,s.__decorate)([(0,o.MZ)({type:Boolean})],M.prototype,"disabled",void 0),(0,s.__decorate)([(0,o.MZ)({type:Boolean})],M.prototype,"required",void 0),(0,s.__decorate)([(0,o.MZ)()],M.prototype,"label",void 0),(0,s.__decorate)([(0,o.MZ)()],M.prototype,"value",void 0),(0,s.__decorate)([(0,o.MZ)()],M.prototype,"helper",void 0),(0,s.__decorate)([(0,o.MZ)()],M.prototype,"placeholder",void 0),(0,s.__decorate)([(0,o.MZ)({attribute:"statistic-types"})],M.prototype,"statisticTypes",void 0),(0,s.__decorate)([(0,o.MZ)({type:Boolean,attribute:"allow-custom-entity"})],M.prototype,"allowCustomEntity",void 0),(0,s.__decorate)([(0,o.MZ)({attribute:!1,type:Array})],M.prototype,"statisticIds",void 0),(0,s.__decorate)([(0,o.MZ)({attribute:!1})],M.prototype,"helpMissingEntityUrl",void 0),(0,s.__decorate)([(0,o.MZ)({type:Array,attribute:"include-statistics-unit-of-measurement"})],M.prototype,"includeStatisticsUnitOfMeasurement",void 0),(0,s.__decorate)([(0,o.MZ)({attribute:"include-unit-class"})],M.prototype,"includeUnitClass",void 0),(0,s.__decorate)([(0,o.MZ)({attribute:"include-device-class"})],M.prototype,"includeDeviceClass",void 0),(0,s.__decorate)([(0,o.MZ)({type:Boolean,attribute:"entities-only"})],M.prototype,"entitiesOnly",void 0),(0,s.__decorate)([(0,o.MZ)({type:Array,attribute:"exclude-statistics"})],M.prototype,"excludeStatistics",void 0),(0,s.__decorate)([(0,o.MZ)({attribute:"hide-clear-icon",type:Boolean})],M.prototype,"hideClearIcon",void 0),(0,s.__decorate)([(0,o.P)("ha-generic-picker")],M.prototype,"_picker",void 0),M=(0,s.__decorate)([(0,o.EM)("ha-statistic-picker")],M),e()}catch(b){e(b)}}))},55917:function(t,e,i){i.a(t,(async function(t,e){try{var s=i(62826),a=i(96196),o=i(77845),n=i(4937),r=i(92542),c=i(60042),l=t([c]);c=(l.then?(await l)():l)[0];class d extends a.WF{render(){if(!this.hass)return a.s6;const t=this.ignoreRestrictionsOnFirstStatistic&&this._currentStatistics.length<=1,e=t?void 0:this.includeStatisticsUnitOfMeasurement,i=t?void 0:this.includeUnitClass,s=t?void 0:this.includeDeviceClass,o=t?void 0:this.statisticTypes;return a.qy`
      ${this.label?a.qy`<label>${this.label}</label>`:a.s6}
      ${(0,n.u)(this._currentStatistics,(t=>t),(t=>a.qy`
          <div>
            <ha-statistic-picker
              .curValue=${t}
              .hass=${this.hass}
              .includeStatisticsUnitOfMeasurement=${e}
              .includeUnitClass=${i}
              .includeDeviceClass=${s}
              .value=${t}
              .statisticTypes=${o}
              .statisticIds=${this.statisticIds}
              .excludeStatistics=${this.value}
              .allowCustomEntity=${this.allowCustomEntity}
              @value-changed=${this._statisticChanged}
            ></ha-statistic-picker>
          </div>
        `))}
      <div>
        <ha-statistic-picker
          .hass=${this.hass}
          .includeStatisticsUnitOfMeasurement=${this.includeStatisticsUnitOfMeasurement}
          .includeUnitClass=${this.includeUnitClass}
          .includeDeviceClass=${this.includeDeviceClass}
          .statisticTypes=${this.statisticTypes}
          .statisticIds=${this.statisticIds}
          .placeholder=${this.placeholder}
          .excludeStatistics=${this.value}
          .allowCustomEntity=${this.allowCustomEntity}
          @value-changed=${this._addStatistic}
        ></ha-statistic-picker>
      </div>
    `}get _currentStatistics(){return this.value||[]}async _updateStatistics(t){this.value=t,(0,r.r)(this,"value-changed",{value:t})}_statisticChanged(t){t.stopPropagation();const e=t.currentTarget.curValue,i=t.detail.value;if(i===e)return;const s=this._currentStatistics;i&&!s.includes(i)?this._updateStatistics(s.map((t=>t===e?i:t))):this._updateStatistics(s.filter((t=>t!==e)))}async _addStatistic(t){t.stopPropagation();const e=t.detail.value;if(!e)return;if(t.currentTarget.value="",!e)return;const i=this._currentStatistics;i.includes(e)||this._updateStatistics([...i,e])}constructor(...t){super(...t),this.ignoreRestrictionsOnFirstStatistic=!1}}d.styles=a.AH`
    :host {
      display: block;
    }
    ha-statistic-picker {
      display: block;
      width: 100%;
      margin-top: 8px;
    }
    label {
      display: block;
      margin-bottom: 0 0 8px;
    }
  `,(0,s.__decorate)([(0,o.MZ)({attribute:!1})],d.prototype,"hass",void 0),(0,s.__decorate)([(0,o.MZ)({type:Array})],d.prototype,"value",void 0),(0,s.__decorate)([(0,o.MZ)({attribute:!1,type:Array})],d.prototype,"statisticIds",void 0),(0,s.__decorate)([(0,o.MZ)({attribute:"statistic-types"})],d.prototype,"statisticTypes",void 0),(0,s.__decorate)([(0,o.MZ)({type:String})],d.prototype,"label",void 0),(0,s.__decorate)([(0,o.MZ)({type:String})],d.prototype,"placeholder",void 0),(0,s.__decorate)([(0,o.MZ)({type:Boolean,attribute:"allow-custom-entity"})],d.prototype,"allowCustomEntity",void 0),(0,s.__decorate)([(0,o.MZ)({attribute:"include-statistics-unit-of-measurement"})],d.prototype,"includeStatisticsUnitOfMeasurement",void 0),(0,s.__decorate)([(0,o.MZ)({attribute:"include-unit-class"})],d.prototype,"includeUnitClass",void 0),(0,s.__decorate)([(0,o.MZ)({attribute:"include-device-class"})],d.prototype,"includeDeviceClass",void 0),(0,s.__decorate)([(0,o.MZ)({type:Boolean,attribute:"ignore-restrictions-on-first-statistic"})],d.prototype,"ignoreRestrictionsOnFirstStatistic",void 0),d=(0,s.__decorate)([(0,o.EM)("ha-statistics-picker")],d),e()}catch(d){e(d)}}))},10675:function(t,e,i){i.a(t,(async function(t,s){try{i.r(e),i.d(e,{HaStatisticSelector:()=>l});var a=i(62826),o=i(96196),n=i(77845),r=i(55917),c=t([r]);r=(c.then?(await c)():c)[0];class l extends o.WF{render(){return this.selector.statistic.multiple?o.qy`
      ${this.label?o.qy`<label>${this.label}</label>`:""}
      <ha-statistics-picker
        .hass=${this.hass}
        .value=${this.value}
        .helper=${this.helper}
        .disabled=${this.disabled}
        .required=${this.required}
      ></ha-statistics-picker>
    `:o.qy`<ha-statistic-picker
        .hass=${this.hass}
        .value=${this.value}
        .label=${this.label}
        .helper=${this.helper}
        .disabled=${this.disabled}
        .required=${this.required}
        allow-custom-entity
      ></ha-statistic-picker>`}constructor(...t){super(...t),this.disabled=!1,this.required=!0}}(0,a.__decorate)([(0,n.MZ)({attribute:!1})],l.prototype,"hass",void 0),(0,a.__decorate)([(0,n.MZ)({attribute:!1})],l.prototype,"selector",void 0),(0,a.__decorate)([(0,n.MZ)()],l.prototype,"value",void 0),(0,a.__decorate)([(0,n.MZ)()],l.prototype,"label",void 0),(0,a.__decorate)([(0,n.MZ)()],l.prototype,"helper",void 0),(0,a.__decorate)([(0,n.MZ)({type:Boolean})],l.prototype,"disabled",void 0),(0,a.__decorate)([(0,n.MZ)({type:Boolean})],l.prototype,"required",void 0),l=(0,a.__decorate)([(0,n.EM)("ha-selector-statistic")],l),s()}catch(l){s(l)}}))},31136:function(t,e,i){i.d(e,{HV:()=>o,Hh:()=>a,KF:()=>r,ON:()=>n,g0:()=>d,s7:()=>c});var s=i(99245);const a="unavailable",o="unknown",n="on",r="off",c=[a,o],l=[a,o,r],d=(0,s.g)(c);(0,s.g)(l)},37157:function(t,e,i){i.d(e,{$O:()=>o,p3:()=>a});var s=i(91889);const a=(t,e)=>t.callWS({type:"recorder/list_statistic_ids",statistic_type:e}),o=(t,e,i)=>{const a=t.states[e];return a?(0,s.u)(a):i?.name||e}},62001:function(t,e,i){i.d(e,{o:()=>s});const s=(t,e)=>`https://${t.config.version.includes("b")?"rc":t.config.version.includes("dev")?"next":"www"}.home-assistant.io${e}`},3890:function(t,e,i){i.d(e,{T:()=>u});var s=i(5055),a=i(63937),o=i(37540);class n{disconnect(){this.G=void 0}reconnect(t){this.G=t}deref(){return this.G}constructor(t){this.G=t}}class r{get(){return this.Y}pause(){this.Y??=new Promise((t=>this.Z=t))}resume(){this.Z?.(),this.Y=this.Z=void 0}constructor(){this.Y=void 0,this.Z=void 0}}var c=i(42017);const l=t=>!(0,a.sO)(t)&&"function"==typeof t.then,d=1073741823;class h extends o.Kq{render(...t){return t.find((t=>!l(t)))??s.c0}update(t,e){const i=this._$Cbt;let a=i.length;this._$Cbt=e;const o=this._$CK,n=this._$CX;this.isConnected||this.disconnected();for(let s=0;s<e.length&&!(s>this._$Cwt);s++){const t=e[s];if(!l(t))return this._$Cwt=s,t;s<a&&t===i[s]||(this._$Cwt=d,a=0,Promise.resolve(t).then((async e=>{for(;n.get();)await n.get();const i=o.deref();if(void 0!==i){const s=i._$Cbt.indexOf(t);s>-1&&s<i._$Cwt&&(i._$Cwt=s,i.setValue(e))}})))}return s.c0}disconnected(){this._$CK.disconnect(),this._$CX.pause()}reconnected(){this._$CK.reconnect(this),this._$CX.resume()}constructor(){super(...arguments),this._$Cwt=d,this._$Cbt=[],this._$CK=new n(this),this._$CX=new r}}const u=(0,c.u$)(h)}};
//# sourceMappingURL=3012.2e9005ad1b523dc3.js.map
/*! For license information please see 1761.dfc88efb0ad37545.js.LICENSE.txt */
export const __webpack_id__="1761";export const __webpack_ids__=["1761"];export const __webpack_modules__={88867:function(e,t,o){o.r(t),o.d(t,{HaIconPicker:()=>_});var i=o(62826),s=o(96196),a=o(77845),r=o(22786),n=o(92542),c=o(33978);o(34887),o(22598),o(94343);let h=[],d=!1;const l=async e=>{try{const t=c.y[e].getIconList;if("function"!=typeof t)return[];const o=await t();return o.map((t=>({icon:`${e}:${t.name}`,parts:new Set(t.name.split("-")),keywords:t.keywords??[]})))}catch(t){return console.warn(`Unable to load icon list for ${e} iconset`),[]}},p=e=>s.qy`
  <ha-combo-box-item type="button">
    <ha-icon .icon=${e.icon} slot="start"></ha-icon>
    ${e.icon}
  </ha-combo-box-item>
`;class _ extends s.WF{render(){return s.qy`
      <ha-combo-box
        .hass=${this.hass}
        item-value-path="icon"
        item-label-path="icon"
        .value=${this._value}
        allow-custom-value
        .dataProvider=${d?this._iconProvider:void 0}
        .label=${this.label}
        .helper=${this.helper}
        .disabled=${this.disabled}
        .required=${this.required}
        .placeholder=${this.placeholder}
        .errorMessage=${this.errorMessage}
        .invalid=${this.invalid}
        .renderer=${p}
        icon
        @opened-changed=${this._openedChanged}
        @value-changed=${this._valueChanged}
      >
        ${this._value||this.placeholder?s.qy`
              <ha-icon .icon=${this._value||this.placeholder} slot="icon">
              </ha-icon>
            `:s.qy`<slot slot="icon" name="fallback"></slot>`}
      </ha-combo-box>
    `}async _openedChanged(e){e.detail.value&&!d&&(await(async()=>{d=!0;const e=await o.e("3451").then(o.t.bind(o,83174,19));h=e.default.map((e=>({icon:`mdi:${e.name}`,parts:new Set(e.name.split("-")),keywords:e.keywords})));const t=[];Object.keys(c.y).forEach((e=>{t.push(l(e))})),(await Promise.all(t)).forEach((e=>{h.push(...e)}))})(),this.requestUpdate())}_valueChanged(e){e.stopPropagation(),this._setValue(e.detail.value)}_setValue(e){this.value=e,(0,n.r)(this,"value-changed",{value:this._value},{bubbles:!1,composed:!1})}get _value(){return this.value||""}constructor(...e){super(...e),this.disabled=!1,this.required=!1,this.invalid=!1,this._filterIcons=(0,r.A)(((e,t=h)=>{if(!e)return t;const o=[],i=(e,t)=>o.push({icon:e,rank:t});for(const s of t)s.parts.has(e)?i(s.icon,1):s.keywords.includes(e)?i(s.icon,2):s.icon.includes(e)?i(s.icon,3):s.keywords.some((t=>t.includes(e)))&&i(s.icon,4);return 0===o.length&&i(e,0),o.sort(((e,t)=>e.rank-t.rank))})),this._iconProvider=(e,t)=>{const o=this._filterIcons(e.filter.toLowerCase(),h),i=e.page*e.pageSize,s=i+e.pageSize;t(o.slice(i,s),o.length)}}}_.styles=s.AH`
    *[slot="icon"] {
      color: var(--primary-text-color);
      position: relative;
      bottom: 2px;
    }
    *[slot="prefix"] {
      margin-right: 8px;
      margin-inline-end: 8px;
      margin-inline-start: initial;
    }
  `,(0,i.__decorate)([(0,a.MZ)({attribute:!1})],_.prototype,"hass",void 0),(0,i.__decorate)([(0,a.MZ)()],_.prototype,"value",void 0),(0,i.__decorate)([(0,a.MZ)()],_.prototype,"label",void 0),(0,i.__decorate)([(0,a.MZ)()],_.prototype,"helper",void 0),(0,i.__decorate)([(0,a.MZ)()],_.prototype,"placeholder",void 0),(0,i.__decorate)([(0,a.MZ)({attribute:"error-message"})],_.prototype,"errorMessage",void 0),(0,i.__decorate)([(0,a.MZ)({type:Boolean})],_.prototype,"disabled",void 0),(0,i.__decorate)([(0,a.MZ)({type:Boolean})],_.prototype,"required",void 0),(0,i.__decorate)([(0,a.MZ)({type:Boolean})],_.prototype,"invalid",void 0),_=(0,i.__decorate)([(0,a.EM)("ha-icon-picker")],_)},66280:function(e,t,o){o.a(e,(async function(e,i){try{o.r(t),o.d(t,{HaIconSelector:()=>p});var s=o(62826),a=o(96196),r=o(77845),n=o(3890),c=o(92542),h=o(43197),d=(o(88867),o(4148)),l=e([d,h]);[d,h]=l.then?(await l)():l;class p extends a.WF{render(){const e=this.context?.icon_entity,t=e?this.hass.states[e]:void 0,o=this.selector.icon?.placeholder||t?.attributes.icon||t&&(0,n.T)((0,h.fq)(this.hass,t));return a.qy`
      <ha-icon-picker
        .hass=${this.hass}
        .label=${this.label}
        .value=${this.value}
        .required=${this.required}
        .disabled=${this.disabled}
        .helper=${this.helper}
        .placeholder=${this.selector.icon?.placeholder??o}
        @value-changed=${this._valueChanged}
      >
        ${!o&&t?a.qy`
              <ha-state-icon
                slot="fallback"
                .hass=${this.hass}
                .stateObj=${t}
              ></ha-state-icon>
            `:a.s6}
      </ha-icon-picker>
    `}_valueChanged(e){(0,c.r)(this,"value-changed",{value:e.detail.value})}constructor(...e){super(...e),this.disabled=!1,this.required=!0}}(0,s.__decorate)([(0,r.MZ)({attribute:!1})],p.prototype,"hass",void 0),(0,s.__decorate)([(0,r.MZ)({attribute:!1})],p.prototype,"selector",void 0),(0,s.__decorate)([(0,r.MZ)()],p.prototype,"value",void 0),(0,s.__decorate)([(0,r.MZ)()],p.prototype,"label",void 0),(0,s.__decorate)([(0,r.MZ)()],p.prototype,"helper",void 0),(0,s.__decorate)([(0,r.MZ)({type:Boolean,reflect:!0})],p.prototype,"disabled",void 0),(0,s.__decorate)([(0,r.MZ)({type:Boolean})],p.prototype,"required",void 0),(0,s.__decorate)([(0,r.MZ)({attribute:!1})],p.prototype,"context",void 0),p=(0,s.__decorate)([(0,r.EM)("ha-selector-icon")],p),i()}catch(p){i(p)}}))},4148:function(e,t,o){o.a(e,(async function(e,t){try{var i=o(62826),s=o(96196),a=o(77845),r=o(3890),n=o(97382),c=o(43197),h=(o(22598),o(60961),e([c]));c=(h.then?(await h)():h)[0];class d extends s.WF{render(){const e=this.icon||this.stateObj&&this.hass?.entities[this.stateObj.entity_id]?.icon||this.stateObj?.attributes.icon;if(e)return s.qy`<ha-icon .icon=${e}></ha-icon>`;if(!this.stateObj)return s.s6;if(!this.hass)return this._renderFallback();const t=(0,c.fq)(this.hass,this.stateObj,this.stateValue).then((e=>e?s.qy`<ha-icon .icon=${e}></ha-icon>`:this._renderFallback()));return s.qy`${(0,r.T)(t)}`}_renderFallback(){const e=(0,n.t)(this.stateObj);return s.qy`
      <ha-svg-icon
        .path=${c.l[e]||c.lW}
      ></ha-svg-icon>
    `}}(0,i.__decorate)([(0,a.MZ)({attribute:!1})],d.prototype,"hass",void 0),(0,i.__decorate)([(0,a.MZ)({attribute:!1})],d.prototype,"stateObj",void 0),(0,i.__decorate)([(0,a.MZ)({attribute:!1})],d.prototype,"stateValue",void 0),(0,i.__decorate)([(0,a.MZ)()],d.prototype,"icon",void 0),d=(0,i.__decorate)([(0,a.EM)("ha-state-icon")],d),t()}catch(d){t(d)}}))},3890:function(e,t,o){o.d(t,{T:()=>p});var i=o(5055),s=o(63937),a=o(37540);class r{disconnect(){this.G=void 0}reconnect(e){this.G=e}deref(){return this.G}constructor(e){this.G=e}}class n{get(){return this.Y}pause(){this.Y??=new Promise((e=>this.Z=e))}resume(){this.Z?.(),this.Y=this.Z=void 0}constructor(){this.Y=void 0,this.Z=void 0}}var c=o(42017);const h=e=>!(0,s.sO)(e)&&"function"==typeof e.then,d=1073741823;class l extends a.Kq{render(...e){return e.find((e=>!h(e)))??i.c0}update(e,t){const o=this._$Cbt;let s=o.length;this._$Cbt=t;const a=this._$CK,r=this._$CX;this.isConnected||this.disconnected();for(let i=0;i<t.length&&!(i>this._$Cwt);i++){const e=t[i];if(!h(e))return this._$Cwt=i,e;i<s&&e===o[i]||(this._$Cwt=d,s=0,Promise.resolve(e).then((async t=>{for(;r.get();)await r.get();const o=a.deref();if(void 0!==o){const i=o._$Cbt.indexOf(e);i>-1&&i<o._$Cwt&&(o._$Cwt=i,o.setValue(t))}})))}return i.c0}disconnected(){this._$CK.disconnect(),this._$CX.pause()}reconnected(){this._$CK.reconnect(this),this._$CX.resume()}constructor(){super(...arguments),this._$Cwt=d,this._$Cbt=[],this._$CK=new r(this),this._$CX=new n}}const p=(0,c.u$)(l)}};
//# sourceMappingURL=1761.dfc88efb0ad37545.js.map
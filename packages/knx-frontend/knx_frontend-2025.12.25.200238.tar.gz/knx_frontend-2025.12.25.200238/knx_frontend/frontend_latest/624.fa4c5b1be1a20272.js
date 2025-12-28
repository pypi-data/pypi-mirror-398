export const __webpack_id__="624";export const __webpack_ids__=["624"];export const __webpack_modules__={88867:function(e,o,t){t.r(o),t.d(o,{HaIconPicker:()=>_});var a=t(62826),i=t(96196),r=t(77845),s=t(22786),n=t(92542),l=t(33978);t(34887),t(22598),t(94343);let c=[],d=!1;const h=async e=>{try{const o=l.y[e].getIconList;if("function"!=typeof o)return[];const t=await o();return t.map((o=>({icon:`${e}:${o.name}`,parts:new Set(o.name.split("-")),keywords:o.keywords??[]})))}catch(o){return console.warn(`Unable to load icon list for ${e} iconset`),[]}},p=e=>i.qy`
  <ha-combo-box-item type="button">
    <ha-icon .icon=${e.icon} slot="start"></ha-icon>
    ${e.icon}
  </ha-combo-box-item>
`;class _ extends i.WF{render(){return i.qy`
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
        ${this._value||this.placeholder?i.qy`
              <ha-icon .icon=${this._value||this.placeholder} slot="icon">
              </ha-icon>
            `:i.qy`<slot slot="icon" name="fallback"></slot>`}
      </ha-combo-box>
    `}async _openedChanged(e){e.detail.value&&!d&&(await(async()=>{d=!0;const e=await t.e("3451").then(t.t.bind(t,83174,19));c=e.default.map((e=>({icon:`mdi:${e.name}`,parts:new Set(e.name.split("-")),keywords:e.keywords})));const o=[];Object.keys(l.y).forEach((e=>{o.push(h(e))})),(await Promise.all(o)).forEach((e=>{c.push(...e)}))})(),this.requestUpdate())}_valueChanged(e){e.stopPropagation(),this._setValue(e.detail.value)}_setValue(e){this.value=e,(0,n.r)(this,"value-changed",{value:this._value},{bubbles:!1,composed:!1})}get _value(){return this.value||""}constructor(...e){super(...e),this.disabled=!1,this.required=!1,this.invalid=!1,this._filterIcons=(0,s.A)(((e,o=c)=>{if(!e)return o;const t=[],a=(e,o)=>t.push({icon:e,rank:o});for(const i of o)i.parts.has(e)?a(i.icon,1):i.keywords.includes(e)?a(i.icon,2):i.icon.includes(e)?a(i.icon,3):i.keywords.some((o=>o.includes(e)))&&a(i.icon,4);return 0===t.length&&a(e,0),t.sort(((e,o)=>e.rank-o.rank))})),this._iconProvider=(e,o)=>{const t=this._filterIcons(e.filter.toLowerCase(),c),a=e.page*e.pageSize,i=a+e.pageSize;o(t.slice(a,i),t.length)}}}_.styles=i.AH`
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
  `,(0,a.__decorate)([(0,r.MZ)({attribute:!1})],_.prototype,"hass",void 0),(0,a.__decorate)([(0,r.MZ)()],_.prototype,"value",void 0),(0,a.__decorate)([(0,r.MZ)()],_.prototype,"label",void 0),(0,a.__decorate)([(0,r.MZ)()],_.prototype,"helper",void 0),(0,a.__decorate)([(0,r.MZ)()],_.prototype,"placeholder",void 0),(0,a.__decorate)([(0,r.MZ)({attribute:"error-message"})],_.prototype,"errorMessage",void 0),(0,a.__decorate)([(0,r.MZ)({type:Boolean})],_.prototype,"disabled",void 0),(0,a.__decorate)([(0,r.MZ)({type:Boolean})],_.prototype,"required",void 0),(0,a.__decorate)([(0,r.MZ)({type:Boolean})],_.prototype,"invalid",void 0),_=(0,a.__decorate)([(0,r.EM)("ha-icon-picker")],_)}};
//# sourceMappingURL=624.fa4c5b1be1a20272.js.map
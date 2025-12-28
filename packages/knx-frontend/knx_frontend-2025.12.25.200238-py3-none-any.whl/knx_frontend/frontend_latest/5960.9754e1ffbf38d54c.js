export const __webpack_id__="5960";export const __webpack_ids__=["5960"];export const __webpack_modules__={81657:function(e,t,a){var o=a(62826),i=a(96196),s=a(77845),r=a(92542);const n=(e,t)=>{const a=(e=>"lovelace"===e.url_path?"panel.states":"profile"===e.url_path?"panel.profile":`panel.${e.title}`)(t);return e.localize(a)||t.title||void 0},l=e=>{if(!e.icon)switch(e.component_name){case"profile":return"mdi:account";case"lovelace":return"mdi:view-dashboard"}return e.icon||void 0};a(34887),a(94343),a(22598);const d=[],h=e=>i.qy`
  <ha-combo-box-item type="button">
    <ha-icon .icon=${e.icon} slot="start"></ha-icon>
    <span slot="headline">${e.title||e.path}</span>
    ${e.title?i.qy`<span slot="supporting-text">${e.path}</span>`:i.s6}
  </ha-combo-box-item>
`,p=(e,t,a)=>{return{path:`/${e}/${t.path??a}`,icon:t.icon??"mdi:view-compact",title:t.title??(t.path?(o=t.path,o.replace(/^_*(.)|_+(.)/g,((e,t,a)=>t?t.toUpperCase():" "+a.toUpperCase()))):`${a}`)};var o},c=(e,t)=>({path:`/${t.url_path}`,icon:l(t)||"mdi:view-dashboard",title:n(e,t)||""});class _ extends i.WF{render(){return i.qy`
      <ha-combo-box
        .hass=${this.hass}
        item-value-path="path"
        item-label-path="path"
        .value=${this._value}
        allow-custom-value
        .filteredItems=${this.navigationItems}
        .label=${this.label}
        .helper=${this.helper}
        .disabled=${this.disabled}
        .required=${this.required}
        .renderer=${h}
        @opened-changed=${this._openedChanged}
        @value-changed=${this._valueChanged}
        @filter-changed=${this._filterChanged}
      >
      </ha-combo-box>
    `}async _openedChanged(e){this._opened=e.detail.value,this._opened&&!this.navigationItemsLoaded&&this._loadNavigationItems()}async _loadNavigationItems(){this.navigationItemsLoaded=!0;const e=Object.entries(this.hass.panels).map((([e,t])=>({id:e,...t}))),t=e.filter((e=>"lovelace"===e.component_name)),a=await Promise.all(t.map((e=>{return(t=this.hass.connection,a="lovelace"===e.url_path?null:e.url_path,o=!0,t.sendMessagePromise({type:"lovelace/config",url_path:a,force:o})).then((t=>[e.id,t])).catch((t=>[e.id,void 0]));var t,a,o}))),o=new Map(a);this.navigationItems=[];for(const i of e){this.navigationItems.push(c(this.hass,i));const e=o.get(i.id);e&&"views"in e&&e.views.forEach(((e,t)=>this.navigationItems.push(p(i.url_path,e,t))))}this.comboBox.filteredItems=this.navigationItems}shouldUpdate(e){return!this._opened||e.has("_opened")}_valueChanged(e){e.stopPropagation(),this._setValue(e.detail.value)}_setValue(e){this.value=e,(0,r.r)(this,"value-changed",{value:this._value},{bubbles:!1,composed:!1})}_filterChanged(e){const t=e.detail.value.toLowerCase();if(t.length>=2){const e=[];this.navigationItems.forEach((a=>{(a.path.toLowerCase().includes(t)||a.title.toLowerCase().includes(t))&&e.push(a)})),e.length>0?this.comboBox.filteredItems=e:this.comboBox.filteredItems=[]}else this.comboBox.filteredItems=this.navigationItems}get _value(){return this.value||""}constructor(...e){super(...e),this.disabled=!1,this.required=!1,this._opened=!1,this.navigationItemsLoaded=!1,this.navigationItems=d}}_.styles=i.AH`
    ha-icon,
    ha-svg-icon {
      color: var(--primary-text-color);
      position: relative;
      bottom: 0px;
    }
    *[slot="prefix"] {
      margin-right: 8px;
      margin-inline-end: 8px;
      margin-inline-start: initial;
    }
  `,(0,o.__decorate)([(0,s.MZ)({attribute:!1})],_.prototype,"hass",void 0),(0,o.__decorate)([(0,s.MZ)()],_.prototype,"label",void 0),(0,o.__decorate)([(0,s.MZ)()],_.prototype,"value",void 0),(0,o.__decorate)([(0,s.MZ)()],_.prototype,"helper",void 0),(0,o.__decorate)([(0,s.MZ)({type:Boolean})],_.prototype,"disabled",void 0),(0,o.__decorate)([(0,s.MZ)({type:Boolean})],_.prototype,"required",void 0),(0,o.__decorate)([(0,s.wk)()],_.prototype,"_opened",void 0),(0,o.__decorate)([(0,s.P)("ha-combo-box",!0)],_.prototype,"comboBox",void 0),_=(0,o.__decorate)([(0,s.EM)("ha-navigation-picker")],_)},79691:function(e,t,a){a.r(t),a.d(t,{HaNavigationSelector:()=>n});var o=a(62826),i=a(96196),s=a(77845),r=a(92542);a(81657);class n extends i.WF{render(){return i.qy`
      <ha-navigation-picker
        .hass=${this.hass}
        .label=${this.label}
        .value=${this.value}
        .required=${this.required}
        .disabled=${this.disabled}
        .helper=${this.helper}
        @value-changed=${this._valueChanged}
      ></ha-navigation-picker>
    `}_valueChanged(e){(0,r.r)(this,"value-changed",{value:e.detail.value})}constructor(...e){super(...e),this.disabled=!1,this.required=!0}}(0,o.__decorate)([(0,s.MZ)({attribute:!1})],n.prototype,"hass",void 0),(0,o.__decorate)([(0,s.MZ)({attribute:!1})],n.prototype,"selector",void 0),(0,o.__decorate)([(0,s.MZ)()],n.prototype,"value",void 0),(0,o.__decorate)([(0,s.MZ)()],n.prototype,"label",void 0),(0,o.__decorate)([(0,s.MZ)()],n.prototype,"helper",void 0),(0,o.__decorate)([(0,s.MZ)({type:Boolean,reflect:!0})],n.prototype,"disabled",void 0),(0,o.__decorate)([(0,s.MZ)({type:Boolean})],n.prototype,"required",void 0),n=(0,o.__decorate)([(0,s.EM)("ha-selector-navigation")],n)}};
//# sourceMappingURL=5960.9754e1ffbf38d54c.js.map
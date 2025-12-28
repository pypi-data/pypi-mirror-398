/*! For license information please see 6080.885021b63c1076ba.js.LICENSE.txt */
export const __webpack_id__="6080";export const __webpack_ids__=["6080"];export const __webpack_modules__={87400:function(e,t,a){a.d(t,{l:()=>s});const s=(e,t,a,s,o)=>{const r=t[e.entity_id];return r?i(r,t,a,s,o):{entity:null,device:null,area:null,floor:null}},i=(e,t,a,s,i)=>{const o=t[e.entity_id],r=e?.device_id,n=r?a[r]:void 0,l=e?.area_id||n?.area_id,d=l?s[l]:void 0,c=d?.floor_id;return{entity:o,device:n||null,area:d||null,floor:(c?i[c]:void 0)||null}}},74529:function(e,t,a){var s=a(62826),i=a(96229),o=a(26069),r=a(91735),n=a(42034),l=a(96196),d=a(77845);class c extends i.k{renderOutline(){return this.filled?l.qy`<span class="filled"></span>`:super.renderOutline()}getContainerClasses(){return{...super.getContainerClasses(),active:this.active}}renderPrimaryContent(){return l.qy`
      <span class="leading icon" aria-hidden="true">
        ${this.renderLeadingIcon()}
      </span>
      <span class="label">${this.label}</span>
      <span class="touch"></span>
      <span class="trailing leading icon" aria-hidden="true">
        ${this.renderTrailingIcon()}
      </span>
    `}renderTrailingIcon(){return l.qy`<slot name="trailing-icon"></slot>`}constructor(...e){super(...e),this.filled=!1,this.active=!1}}c.styles=[r.R,n.R,o.R,l.AH`
      :host {
        --md-sys-color-primary: var(--primary-text-color);
        --md-sys-color-on-surface: var(--primary-text-color);
        --md-assist-chip-container-shape: var(
          --ha-assist-chip-container-shape,
          16px
        );
        --md-assist-chip-outline-color: var(--outline-color);
        --md-assist-chip-label-text-weight: 400;
      }
      /** Material 3 doesn't have a filled chip, so we have to make our own **/
      .filled {
        display: flex;
        pointer-events: none;
        border-radius: inherit;
        inset: 0;
        position: absolute;
        background-color: var(--ha-assist-chip-filled-container-color);
      }
      /** Set the size of mdc icons **/
      ::slotted([slot="icon"]),
      ::slotted([slot="trailing-icon"]) {
        display: flex;
        --mdc-icon-size: var(--md-input-chip-icon-size, 18px);
        font-size: var(--_label-text-size) !important;
      }

      .trailing.icon ::slotted(*),
      .trailing.icon svg {
        margin-inline-end: unset;
        margin-inline-start: var(--_icon-label-space);
      }
      ::before {
        background: var(--ha-assist-chip-container-color, transparent);
        opacity: var(--ha-assist-chip-container-opacity, 1);
      }
      :where(.active)::before {
        background: var(--ha-assist-chip-active-container-color);
        opacity: var(--ha-assist-chip-active-container-opacity);
      }
      .label {
        font-family: var(--ha-font-family-body);
      }
    `],(0,s.__decorate)([(0,d.MZ)({type:Boolean,reflect:!0})],c.prototype,"filled",void 0),(0,s.__decorate)([(0,d.MZ)({type:Boolean})],c.prototype,"active",void 0),c=(0,s.__decorate)([(0,d.EM)("ha-assist-chip")],c)},27891:function(e,t,a){a.r(t),a.d(t,{HaSelectorEntityName:()=>f});var s=a(62826),i=a(96196),o=a(77845),r=a(10085),n=(a(1106),a(78648)),l=a(4937),d=a(22786),c=a(55376),h=a(92542),p=a(55124),u=a(87400);a(74529),a(96294),a(25388),a(34887),a(56768),a(63801);const v=e=>i.qy`
  <ha-combo-box-item type="button">
    <span slot="headline">${e.primary}</span>
    ${e.secondary?i.qy`<span slot="supporting-text">${e.secondary}</span>`:i.s6}
  </ha-combo-box-item>
`,_=new Set(["entity","device","area","floor"]),m=new Set(["entity","device","area","floor"]),b=e=>"text"===e.type&&e.text?e.text:`___${e.type}___`;class y extends i.WF{render(){const e=this._items,t=this._getOptions(this.entityId),a=this._validTypes(this.entityId);return i.qy`
      ${this.label?i.qy`<label>${this.label}</label>`:i.s6}
      <div class="container">
        <ha-sortable
          no-style
          @item-moved=${this._moveItem}
          .disabled=${this.disabled}
          handle-selector="button.primary.action"
          filter=".add"
        >
          <ha-chip-set>
            ${(0,l.u)(this._items,(e=>e),((e,t)=>{const s=this._formatItem(e),o=a.has(e.type);return i.qy`
                  <ha-input-chip
                    data-idx=${t}
                    @remove=${this._removeItem}
                    @click=${this._editItem}
                    .label=${s}
                    .selected=${!this.disabled}
                    .disabled=${this.disabled}
                    class=${o?"":"invalid"}
                  >
                    <ha-svg-icon
                      slot="icon"
                      .path=${"M21 11H3V9H21V11M21 13H3V15H21V13Z"}
                    ></ha-svg-icon>
                    <span>${s}</span>
                  </ha-input-chip>
                `}))}
            ${this.disabled?i.s6:i.qy`
                  <ha-assist-chip
                    @click=${this._addItem}
                    .disabled=${this.disabled}
                    label=${this.hass.localize("ui.components.entity.entity-name-picker.add")}
                    class="add"
                  >
                    <ha-svg-icon slot="icon" .path=${"M19,13H13V19H11V13H5V11H11V5H13V11H19V13Z"}></ha-svg-icon>
                  </ha-assist-chip>
                `}
          </ha-chip-set>
        </ha-sortable>

        <mwc-menu-surface
          .open=${this._opened}
          @closed=${this._onClosed}
          @opened=${this._onOpened}
          @input=${p.d}
          .anchor=${this._container}
        >
          <ha-combo-box
            .hass=${this.hass}
            .value=${""}
            .autofocus=${this.autofocus}
            .disabled=${this.disabled}
            .required=${this.required&&!e.length}
            .items=${t}
            allow-custom-value
            item-id-path="value"
            item-value-path="value"
            item-label-path="field_label"
            .renderer=${v}
            @opened-changed=${this._openedChanged}
            @value-changed=${this._comboBoxValueChanged}
            @filter-changed=${this._filterChanged}
          >
          </ha-combo-box>
        </mwc-menu-surface>
      </div>
      ${this._renderHelper()}
    `}_renderHelper(){return this.helper?i.qy`
          <ha-input-helper-text .disabled=${this.disabled}>
            ${this.helper}
          </ha-input-helper-text>
        `:i.s6}_onClosed(e){e.stopPropagation(),this._opened=!1,this._editIndex=void 0}async _onOpened(e){this._opened&&(e.stopPropagation(),this._opened=!0,await(this._comboBox?.focus()),await(this._comboBox?.open()))}async _addItem(e){e.stopPropagation(),this._opened=!0}async _editItem(e){e.stopPropagation();const t=parseInt(e.currentTarget.dataset.idx,10);this._editIndex=t,this._opened=!0}get _items(){return this._toItems(this.value)}_openedChanged(e){if(e.detail.value){const e=this._comboBox.items||[],t=null!=this._editIndex?this._items[this._editIndex]:void 0,a=t?b(t):"",s=this._filterSelectedOptions(e,a);"text"===t?.type&&t.text&&s.push(this._customNameOption(t.text)),this._comboBox.filteredItems=s,this._comboBox.setInputValue(a)}else this._opened=!1,this._comboBox.setInputValue("")}_filterChanged(e){const t=e.detail.value,a=t?.toLowerCase()||"",s=this._comboBox.items||[],i=null!=this._editIndex?this._items[this._editIndex]:void 0,o=i?b(i):"";let r=this._filterSelectedOptions(s,o);if(!a)return void(this._comboBox.filteredItems=r);const l={keys:["primary","secondary","value"],isCaseSensitive:!1,minMatchCharLength:Math.min(a.length,2),threshold:.2,ignoreDiacritics:!0};r=new n.A(r,l).search(a).map((e=>e.item)),r.push(this._customNameOption(t)),this._comboBox.filteredItems=r}async _moveItem(e){e.stopPropagation();const{oldIndex:t,newIndex:a}=e.detail,s=this._items.concat(),i=s.splice(t,1)[0];s.splice(a,0,i),this._setValue(s),await this.updateComplete,this._filterChanged({detail:{value:""}})}async _removeItem(e){e.stopPropagation();const t=[...this._items],a=parseInt(e.target.dataset.idx,10);t.splice(a,1),this._setValue(t),await this.updateComplete,this._filterChanged({detail:{value:""}})}_comboBoxValueChanged(e){e.stopPropagation();const t=e.detail.value;if(this.disabled||""===t)return;const a=(e=>{if(e.startsWith("___")&&e.endsWith("___")){const t=e.slice(3,-3);if(_.has(t))return{type:t}}return{type:"text",text:e}})(t),s=[...this._items];null!=this._editIndex?s[this._editIndex]=a:s.push(a),this._setValue(s)}_setValue(e){const t=this._toValue(e);this.value=t,(0,h.r)(this,"value-changed",{value:t})}constructor(...e){super(...e),this.required=!1,this.disabled=!1,this._opened=!1,this._validTypes=(0,d.A)((e=>{const t=new Set(["text"]);if(!e)return t;const a=this.hass.states[e];if(!a)return t;t.add("entity");const s=(0,u.l)(a,this.hass.entities,this.hass.devices,this.hass.areas,this.hass.floors);return s.device&&t.add("device"),s.area&&t.add("area"),s.floor&&t.add("floor"),t})),this._getOptions=(0,d.A)((e=>{if(!e)return[];const t=this._validTypes(e);return["entity","device","area","floor"].map((a=>{const s=this.hass.states[e],i=t.has(a),o=this.hass.localize(`ui.components.entity.entity-name-picker.types.${a}`);return{primary:o,secondary:(s&&i?this.hass.formatEntityName(s,{type:a}):this.hass.localize(`ui.components.entity.entity-name-picker.types.${a}_missing`))||"-",field_label:o,value:b({type:a})}}))})),this._customNameOption=(0,d.A)((e=>({primary:this.hass.localize("ui.components.entity.entity-name-picker.custom_name"),secondary:`"${e}"`,field_label:e,value:b({type:"text",text:e})}))),this._formatItem=e=>"text"===e.type?`"${e.text}"`:_.has(e.type)?this.hass.localize(`ui.components.entity.entity-name-picker.types.${e.type}`):e.type,this._toItems=(0,d.A)((e=>"string"==typeof e?""===e?[]:[{type:"text",text:e}]:e?(0,c.e)(e):[])),this._toValue=(0,d.A)((e=>{if(0!==e.length){if(1===e.length){const t=e[0];return"text"===t.type?t.text:t}return e}})),this._filterSelectedOptions=(e,t)=>{const a=this._items,s=new Set(a.filter((e=>m.has(e.type))).map((e=>b(e))));return e.filter((e=>!s.has(e.value)||e.value===t))}}}y.styles=i.AH`
    :host {
      position: relative;
      width: 100%;
    }

    .container {
      position: relative;
      background-color: var(--mdc-text-field-fill-color, whitesmoke);
      border-radius: var(--ha-border-radius-sm);
      border-end-end-radius: var(--ha-border-radius-square);
      border-end-start-radius: var(--ha-border-radius-square);
    }
    .container:after {
      display: block;
      content: "";
      position: absolute;
      pointer-events: none;
      bottom: 0;
      left: 0;
      right: 0;
      height: 1px;
      width: 100%;
      background-color: var(
        --mdc-text-field-idle-line-color,
        rgba(0, 0, 0, 0.42)
      );
      transform:
        height 180ms ease-in-out,
        background-color 180ms ease-in-out;
    }
    :host([disabled]) .container:after {
      background-color: var(
        --mdc-text-field-disabled-line-color,
        rgba(0, 0, 0, 0.42)
      );
    }
    .container:focus-within:after {
      height: 2px;
      background-color: var(--mdc-theme-primary);
    }

    label {
      display: block;
      margin: 0 0 var(--ha-space-2);
    }

    .add {
      order: 1;
    }

    mwc-menu-surface {
      --mdc-menu-min-width: 100%;
    }

    ha-chip-set {
      padding: var(--ha-space-2) var(--ha-space-2);
    }

    .invalid {
      text-decoration: line-through;
    }

    .sortable-fallback {
      display: none;
      opacity: 0;
    }

    .sortable-ghost {
      opacity: 0.4;
    }

    .sortable-drag {
      cursor: grabbing;
    }

    ha-input-helper-text {
      display: block;
      margin: var(--ha-space-2) 0 0;
    }
  `,(0,s.__decorate)([(0,o.MZ)({attribute:!1})],y.prototype,"hass",void 0),(0,s.__decorate)([(0,o.MZ)({attribute:!1})],y.prototype,"entityId",void 0),(0,s.__decorate)([(0,o.MZ)({attribute:!1})],y.prototype,"value",void 0),(0,s.__decorate)([(0,o.MZ)()],y.prototype,"label",void 0),(0,s.__decorate)([(0,o.MZ)()],y.prototype,"helper",void 0),(0,s.__decorate)([(0,o.MZ)({type:Boolean})],y.prototype,"required",void 0),(0,s.__decorate)([(0,o.MZ)({type:Boolean,reflect:!0})],y.prototype,"disabled",void 0),(0,s.__decorate)([(0,o.P)(".container",!0)],y.prototype,"_container",void 0),(0,s.__decorate)([(0,o.P)("ha-combo-box",!0)],y.prototype,"_comboBox",void 0),(0,s.__decorate)([(0,o.wk)()],y.prototype,"_opened",void 0),y=(0,s.__decorate)([(0,o.EM)("ha-entity-name-picker")],y);class f extends((0,r.E)(i.WF)){render(){const e=this.value??this.selector.entity_name?.default_name;return i.qy`
      <ha-entity-name-picker
        .hass=${this.hass}
        .entityId=${this.selector.entity_name?.entity_id||this.context?.entity}
        .value=${e}
        .label=${this.label}
        .helper=${this.helper}
        .disabled=${this.disabled}
        .required=${this.required}
      ></ha-entity-name-picker>
    `}constructor(...e){super(...e),this.disabled=!1,this.required=!0}}(0,s.__decorate)([(0,o.MZ)({attribute:!1})],f.prototype,"hass",void 0),(0,s.__decorate)([(0,o.MZ)({attribute:!1})],f.prototype,"selector",void 0),(0,s.__decorate)([(0,o.MZ)()],f.prototype,"value",void 0),(0,s.__decorate)([(0,o.MZ)()],f.prototype,"label",void 0),(0,s.__decorate)([(0,o.MZ)()],f.prototype,"helper",void 0),(0,s.__decorate)([(0,o.MZ)({type:Boolean})],f.prototype,"disabled",void 0),(0,s.__decorate)([(0,o.MZ)({type:Boolean})],f.prototype,"required",void 0),(0,s.__decorate)([(0,o.MZ)({attribute:!1})],f.prototype,"context",void 0),f=(0,s.__decorate)([(0,o.EM)("ha-selector-entity_name")],f)},10085:function(e,t,a){a.d(t,{E:()=>o});var s=a(62826),i=a(77845);const o=e=>{class t extends e{connectedCallback(){super.connectedCallback(),this._checkSubscribed()}disconnectedCallback(){if(super.disconnectedCallback(),this.__unsubs){for(;this.__unsubs.length;){const e=this.__unsubs.pop();e instanceof Promise?e.then((e=>e())):e()}this.__unsubs=void 0}}updated(e){if(super.updated(e),e.has("hass"))this._checkSubscribed();else if(this.hassSubscribeRequiredHostProps)for(const t of e.keys())if(this.hassSubscribeRequiredHostProps.includes(t))return void this._checkSubscribed()}hassSubscribe(){return[]}_checkSubscribed(){void 0===this.__unsubs&&this.isConnected&&void 0!==this.hass&&!this.hassSubscribeRequiredHostProps?.some((e=>void 0===this[e]))&&(this.__unsubs=this.hassSubscribe())}}return(0,s.__decorate)([(0,i.MZ)({attribute:!1})],t.prototype,"hass",void 0),t}},96229:function(e,t,a){a.d(t,{k:()=>n});var s=a(62826),i=(a(83461),a(96196)),o=a(77845),r=a(99591);class n extends r.v{get primaryId(){return this.href?"link":"button"}get rippleDisabled(){return!this.href&&(this.disabled||this.softDisabled)}getContainerClasses(){return{...super.getContainerClasses(),disabled:!this.href&&(this.disabled||this.softDisabled),elevated:this.elevated,link:!!this.href}}renderPrimaryAction(e){const{ariaLabel:t}=this;return this.href?i.qy`
        <a
          class="primary action"
          id="link"
          aria-label=${t||i.s6}
          href=${this.href}
          download=${this.download||i.s6}
          target=${this.target||i.s6}
          >${e}</a
        >
      `:i.qy`
      <button
        class="primary action"
        id="button"
        aria-label=${t||i.s6}
        aria-disabled=${this.softDisabled||i.s6}
        ?disabled=${this.disabled&&!this.alwaysFocusable}
        type="button"
        >${e}</button
      >
    `}renderOutline(){return this.elevated?i.qy`<md-elevation part="elevation"></md-elevation>`:super.renderOutline()}constructor(){super(...arguments),this.elevated=!1,this.href="",this.download="",this.target=""}}(0,s.__decorate)([(0,o.MZ)({type:Boolean})],n.prototype,"elevated",void 0),(0,s.__decorate)([(0,o.MZ)()],n.prototype,"href",void 0),(0,s.__decorate)([(0,o.MZ)()],n.prototype,"download",void 0),(0,s.__decorate)([(0,o.MZ)()],n.prototype,"target",void 0)},26069:function(e,t,a){a.d(t,{R:()=>s});const s=a(96196).AH`:host{--_container-height: var(--md-assist-chip-container-height, 32px);--_disabled-label-text-color: var(--md-assist-chip-disabled-label-text-color, var(--md-sys-color-on-surface, #1d1b20));--_disabled-label-text-opacity: var(--md-assist-chip-disabled-label-text-opacity, 0.38);--_elevated-container-color: var(--md-assist-chip-elevated-container-color, var(--md-sys-color-surface-container-low, #f7f2fa));--_elevated-container-elevation: var(--md-assist-chip-elevated-container-elevation, 1);--_elevated-container-shadow-color: var(--md-assist-chip-elevated-container-shadow-color, var(--md-sys-color-shadow, #000));--_elevated-disabled-container-color: var(--md-assist-chip-elevated-disabled-container-color, var(--md-sys-color-on-surface, #1d1b20));--_elevated-disabled-container-elevation: var(--md-assist-chip-elevated-disabled-container-elevation, 0);--_elevated-disabled-container-opacity: var(--md-assist-chip-elevated-disabled-container-opacity, 0.12);--_elevated-focus-container-elevation: var(--md-assist-chip-elevated-focus-container-elevation, 1);--_elevated-hover-container-elevation: var(--md-assist-chip-elevated-hover-container-elevation, 2);--_elevated-pressed-container-elevation: var(--md-assist-chip-elevated-pressed-container-elevation, 1);--_focus-label-text-color: var(--md-assist-chip-focus-label-text-color, var(--md-sys-color-on-surface, #1d1b20));--_hover-label-text-color: var(--md-assist-chip-hover-label-text-color, var(--md-sys-color-on-surface, #1d1b20));--_hover-state-layer-color: var(--md-assist-chip-hover-state-layer-color, var(--md-sys-color-on-surface, #1d1b20));--_hover-state-layer-opacity: var(--md-assist-chip-hover-state-layer-opacity, 0.08);--_label-text-color: var(--md-assist-chip-label-text-color, var(--md-sys-color-on-surface, #1d1b20));--_label-text-font: var(--md-assist-chip-label-text-font, var(--md-sys-typescale-label-large-font, var(--md-ref-typeface-plain, Roboto)));--_label-text-line-height: var(--md-assist-chip-label-text-line-height, var(--md-sys-typescale-label-large-line-height, 1.25rem));--_label-text-size: var(--md-assist-chip-label-text-size, var(--md-sys-typescale-label-large-size, 0.875rem));--_label-text-weight: var(--md-assist-chip-label-text-weight, var(--md-sys-typescale-label-large-weight, var(--md-ref-typeface-weight-medium, 500)));--_pressed-label-text-color: var(--md-assist-chip-pressed-label-text-color, var(--md-sys-color-on-surface, #1d1b20));--_pressed-state-layer-color: var(--md-assist-chip-pressed-state-layer-color, var(--md-sys-color-on-surface, #1d1b20));--_pressed-state-layer-opacity: var(--md-assist-chip-pressed-state-layer-opacity, 0.12);--_disabled-outline-color: var(--md-assist-chip-disabled-outline-color, var(--md-sys-color-on-surface, #1d1b20));--_disabled-outline-opacity: var(--md-assist-chip-disabled-outline-opacity, 0.12);--_focus-outline-color: var(--md-assist-chip-focus-outline-color, var(--md-sys-color-on-surface, #1d1b20));--_outline-color: var(--md-assist-chip-outline-color, var(--md-sys-color-outline, #79747e));--_outline-width: var(--md-assist-chip-outline-width, 1px);--_disabled-leading-icon-color: var(--md-assist-chip-disabled-leading-icon-color, var(--md-sys-color-on-surface, #1d1b20));--_disabled-leading-icon-opacity: var(--md-assist-chip-disabled-leading-icon-opacity, 0.38);--_focus-leading-icon-color: var(--md-assist-chip-focus-leading-icon-color, var(--md-sys-color-primary, #6750a4));--_hover-leading-icon-color: var(--md-assist-chip-hover-leading-icon-color, var(--md-sys-color-primary, #6750a4));--_leading-icon-color: var(--md-assist-chip-leading-icon-color, var(--md-sys-color-primary, #6750a4));--_icon-size: var(--md-assist-chip-icon-size, 18px);--_pressed-leading-icon-color: var(--md-assist-chip-pressed-leading-icon-color, var(--md-sys-color-primary, #6750a4));--_container-shape-start-start: var(--md-assist-chip-container-shape-start-start, var(--md-assist-chip-container-shape, var(--md-sys-shape-corner-small, 8px)));--_container-shape-start-end: var(--md-assist-chip-container-shape-start-end, var(--md-assist-chip-container-shape, var(--md-sys-shape-corner-small, 8px)));--_container-shape-end-end: var(--md-assist-chip-container-shape-end-end, var(--md-assist-chip-container-shape, var(--md-sys-shape-corner-small, 8px)));--_container-shape-end-start: var(--md-assist-chip-container-shape-end-start, var(--md-assist-chip-container-shape, var(--md-sys-shape-corner-small, 8px)));--_leading-space: var(--md-assist-chip-leading-space, 16px);--_trailing-space: var(--md-assist-chip-trailing-space, 16px);--_icon-label-space: var(--md-assist-chip-icon-label-space, 8px);--_with-leading-icon-leading-space: var(--md-assist-chip-with-leading-icon-leading-space, 8px)}@media(forced-colors: active){.link .outline{border-color:ActiveText}}
`}};
//# sourceMappingURL=6080.885021b63c1076ba.js.map
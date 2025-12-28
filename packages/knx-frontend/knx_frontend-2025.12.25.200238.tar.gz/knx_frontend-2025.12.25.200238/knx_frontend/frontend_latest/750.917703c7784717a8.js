export const __webpack_id__="750";export const __webpack_ids__=["750"];export const __webpack_modules__={12109:function(t,e,i){var o=i(62826),s=i(96196),a=i(77845);class l extends s.WF{render(){return s.qy`<slot></slot>`}}l.styles=s.AH`
    :host {
      background-color: var(--ha-color-fill-neutral-quiet-resting);
      padding: var(--ha-space-1) var(--ha-space-2);
      font-weight: var(--ha-font-weight-bold);
      color: var(--secondary-text-color);
      min-height: var(--ha-space-6);
      display: flex;
      align-items: center;
      box-sizing: border-box;
    }
  `,l=(0,o.__decorate)([(0,a.EM)("ha-section-title")],l)},17262:function(t,e,i){var o=i(62826),s=i(96196),a=i(77845),l=(i(60733),i(60961),i(78740),i(92542));class r extends s.WF{focus(){this._input?.focus()}render(){return s.qy`
      <ha-textfield
        .autofocus=${this.autofocus}
        autocomplete="off"
        .label=${this.label||this.hass.localize("ui.common.search")}
        .value=${this.filter||""}
        icon
        .iconTrailing=${this.filter||this.suffix}
        @input=${this._filterInputChanged}
      >
        <slot name="prefix" slot="leadingIcon">
          <ha-svg-icon
            tabindex="-1"
            class="prefix"
            .path=${"M9.5,3A6.5,6.5 0 0,1 16,9.5C16,11.11 15.41,12.59 14.44,13.73L14.71,14H15.5L20.5,19L19,20.5L14,15.5V14.71L13.73,14.44C12.59,15.41 11.11,16 9.5,16A6.5,6.5 0 0,1 3,9.5A6.5,6.5 0 0,1 9.5,3M9.5,5C7,5 5,7 5,9.5C5,12 7,14 9.5,14C12,14 14,12 14,9.5C14,7 12,5 9.5,5Z"}
          ></ha-svg-icon>
        </slot>
        <div class="trailing" slot="trailingIcon">
          ${this.filter&&s.qy`
            <ha-icon-button
              @click=${this._clearSearch}
              .label=${this.hass.localize("ui.common.clear")}
              .path=${"M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z"}
              class="clear-button"
            ></ha-icon-button>
          `}
          <slot name="suffix"></slot>
        </div>
      </ha-textfield>
    `}async _filterChanged(t){(0,l.r)(this,"value-changed",{value:String(t)})}async _filterInputChanged(t){this._filterChanged(t.target.value)}async _clearSearch(){this._filterChanged("")}constructor(...t){super(...t),this.suffix=!1,this.autofocus=!1}}r.styles=s.AH`
    :host {
      display: inline-flex;
    }
    ha-svg-icon,
    ha-icon-button {
      color: var(--primary-text-color);
    }
    ha-svg-icon {
      outline: none;
    }
    .clear-button {
      --mdc-icon-size: 20px;
    }
    ha-textfield {
      display: inherit;
    }
    .trailing {
      display: flex;
      align-items: center;
    }
  `,(0,o.__decorate)([(0,a.MZ)({attribute:!1})],r.prototype,"hass",void 0),(0,o.__decorate)([(0,a.MZ)()],r.prototype,"filter",void 0),(0,o.__decorate)([(0,a.MZ)({type:Boolean})],r.prototype,"suffix",void 0),(0,o.__decorate)([(0,a.MZ)({type:Boolean})],r.prototype,"autofocus",void 0),(0,o.__decorate)([(0,a.MZ)({type:String})],r.prototype,"label",void 0),(0,o.__decorate)([(0,a.P)("ha-textfield",!0)],r.prototype,"_input",void 0),r=(0,o.__decorate)([(0,a.EM)("search-input")],r)},42957:function(t,e,i){i.a(t,(async function(t,o){try{i.r(e),i.d(e,{KnxDptSelectDialog:()=>_});var s=i(62826),a=i(22786),l=i(96196),r=i(77845),n=i(36626),c=i(89473),d=(i(5841),i(17262),i(42921),i(23897),i(12109),i(92542)),h=i(39396),p=i(19337),u=t([n,c]);[n,c]=u.then?(await u)():u;class _ extends l.WF{async showDialog(t){this._params=t,this.dpts=t.dpts??{},this._selected=t.initialSelection??this._selected,this._open=!0}closeDialog(t){return this._dialogClosed(),!0}_cancel(){this._selected=void 0,this._params?.onClose&&this._params.onClose(void 0),this._dialogClosed()}_confirm(){this._params?.onClose&&this._params.onClose(this._selected),this._dialogClosed()}_itemKeydown(t){if("Enter"===t.key){t.preventDefault();const e=t.currentTarget.getAttribute("value");this._selected=e??void 0,this._confirm()}}_onDoubleClick(t){const e=t.currentTarget.getAttribute("value");this._selected=e??void 0,this._selected&&this._confirm()}_onSelect(t){const e=t.currentTarget.getAttribute("value");this._selected=e??void 0}_onFilterChanged(t){this._filter=t.detail?.value??""}_getDptInfo(t){const e=this.dpts[t];return{label:this.hass.localize(`component.knx.config_panel.dpt.options.${t.replace(".","_")}`)??e?.name??this.hass.localize("state.default.unknown"),unit:e?.unit??""}}_dialogClosed(){this._open=!1,this._params=void 0,this._filter="",this._selected=void 0,(0,d.r)(this,"dialog-closed",{dialog:this.localName})}render(){if(!this._params||!this.hass)return l.s6;const t=this._params.width??"medium";return l.qy` <ha-wa-dialog
      .hass=${this.hass}
      .open=${this._open}
      width=${t}
      .headerTitle=${this._params.title}
      @closed=${this._dialogClosed}
    >
      <div class="dialog-body">
        <search-input
          ?autofocus=${!0}
          .hass=${this.hass}
          .filter=${this._filter}
          @value-changed=${this._onFilterChanged}
          .label=${this.hass.localize("ui.common.search")??"Search"}
        ></search-input>

        ${Object.keys(this.dpts).length?l.qy`<div class="dpt-list-container">
              ${this._groupDpts(this._filter,this.dpts).map((t=>l.qy`
                  ${t.title?l.qy`<ha-section-title>${t.title}</ha-section-title>`:l.s6}
                  <ha-md-list>
                    ${t.items.map((t=>{const e=this._getDptInfo(t),i=this._selected===t;return l.qy`<ha-md-list-item
                        interactive
                        type="button"
                        value=${t}
                        @click=${this._onSelect}
                        @dblclick=${this._onDoubleClick}
                        @keydown=${this._itemKeydown}
                      >
                        <div class="dpt-row ${i?"selected":""}" slot="headline">
                          <div class="dpt-number">${t}</div>
                          <div class="dpt-name">${e.label}</div>
                          <div class="dpt-unit">${e.unit}</div>
                        </div>
                      </ha-md-list-item>`}))}
                  </ha-md-list>
                `))}
            </div>`:l.qy`<div>No options</div>`}
      </div>

      <ha-dialog-footer slot="footer">
        <ha-button slot="secondaryAction" appearance="plain" @click=${this._cancel}>
          ${this.hass.localize("ui.common.cancel")??"Cancel"}
        </ha-button>
        <ha-button slot="primaryAction" @click=${this._confirm} .disabled=${!this._selected}>
          ${this.hass.localize("ui.common.ok")??"OK"}
        </ha-button>
      </ha-dialog-footer>
    </ha-wa-dialog>`}static get styles(){return[h.nA,l.AH`
        @media all and (min-width: 600px) {
          ha-wa-dialog {
            --mdc-dialog-min-width: 360px;
          }
        }

        .dialog-body {
          display: flex;
          flex-direction: column;
          gap: var(--ha-space-2, 8px);
          height: 100%;
          min-height: 0;
        }

        search-input {
          display: block;
          width: 100%;
        }

        .dpt-list-container {
          flex: 1 1 auto;
          min-height: 0;
          overflow: auto;
          border: 1px solid var(--divider-color);
          border-radius: 4px;
        }

        .dpt-row {
          display: grid;
          grid-template-columns: 8ch minmax(0, 1fr) auto;
          align-items: center;
          gap: var(--ha-space-2, 8px);
          padding: 6px 8px;
          border-radius: 4px;
        }

        .dpt-row.selected {
          background-color: rgba(var(--rgb-primary-color), 0.08);
          outline: 2px solid rgba(var(--rgb-accent-color), 0.12);
        }

        .dpt-number {
          font-family:
            ui-monospace, SFMono-Regular, Menlo, Monaco, "Roboto Mono", "Courier New", monospace;
          width: 100%;
          color: var(--secondary-text-color);
          white-space: nowrap;
        }

        .dpt-name {
          font-weight: 500;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
          min-width: 0;
        }

        .dpt-unit {
          text-align: right;
          color: var(--secondary-text-color);
          white-space: nowrap;
        }
      `]}constructor(...t){super(...t),this._open=!1,this.dpts={},this._filter="",this._groupDpts=(0,a.A)(((t,e)=>{const i=new Map,o=t.trim().toLowerCase();for(const s of Object.keys(e)){const t=this._getDptInfo(s);if(o){const e=s.toLowerCase().includes(o),i=t.label?.toLowerCase().includes(o),a=!!t.unit&&t.unit.toLowerCase().includes(o);if(!e&&!i&&!a)continue}const e=`${String(s).split(".",1)[0]||s}`;i.has(e)||i.set(e,[]),i.get(e).push(s)}return Array.from(i.entries()).sort(((t,e)=>{const i=Number(t[0]),o=Number(e[0]);return Number.isNaN(i)||Number.isNaN(o)?t[0].localeCompare(e[0]):i-o})).map((([t,e])=>({title:`${t}.*`,items:e.sort(((t,e)=>{const i=(0,p.$k)(t),o=(0,p.$k)(e);return i&&o?(0,p._O)(i,o):i?-1:o?1:t.localeCompare(e)}))})))}))}}(0,s.__decorate)([(0,r.MZ)({attribute:!1})],_.prototype,"hass",void 0),(0,s.__decorate)([(0,r.wk)()],_.prototype,"_open",void 0),(0,s.__decorate)([(0,r.wk)()],_.prototype,"_params",void 0),(0,s.__decorate)([(0,r.wk)()],_.prototype,"dpts",void 0),(0,s.__decorate)([(0,r.wk)()],_.prototype,"_selected",void 0),(0,s.__decorate)([(0,r.wk)()],_.prototype,"_filter",void 0),_=(0,s.__decorate)([(0,r.EM)("knx-dpt-select-dialog")],_),o()}catch(_){o(_)}}))}};
//# sourceMappingURL=750.917703c7784717a8.js.map
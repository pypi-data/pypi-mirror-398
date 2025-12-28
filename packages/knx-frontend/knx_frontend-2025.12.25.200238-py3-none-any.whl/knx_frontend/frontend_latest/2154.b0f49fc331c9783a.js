export const __webpack_id__="2154";export const __webpack_ids__=["2154"];export const __webpack_modules__={17262:function(e,t,i){var o=i(62826),s=i(96196),a=i(77845),r=(i(60733),i(60961),i(78740),i(92542));class l extends s.WF{focus(){this._input?.focus()}render(){return s.qy`
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
    `}async _filterChanged(e){(0,r.r)(this,"value-changed",{value:String(e)})}async _filterInputChanged(e){this._filterChanged(e.target.value)}async _clearSearch(){this._filterChanged("")}constructor(...e){super(...e),this.suffix=!1,this.autofocus=!1}}l.styles=s.AH`
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
  `,(0,o.__decorate)([(0,a.MZ)({attribute:!1})],l.prototype,"hass",void 0),(0,o.__decorate)([(0,a.MZ)()],l.prototype,"filter",void 0),(0,o.__decorate)([(0,a.MZ)({type:Boolean})],l.prototype,"suffix",void 0),(0,o.__decorate)([(0,a.MZ)({type:Boolean})],l.prototype,"autofocus",void 0),(0,o.__decorate)([(0,a.MZ)({type:String})],l.prototype,"label",void 0),(0,o.__decorate)([(0,a.P)("ha-textfield",!0)],l.prototype,"_input",void 0),l=(0,o.__decorate)([(0,a.EM)("search-input")],l)},193:function(e,t,i){i.a(e,(async function(e,o){try{i.r(t),i.d(t,{KnxGaSelectDialog:()=>u});var s=i(62826),a=i(22786),r=i(96196),l=i(77845),n=i(94333),d=i(36626),c=i(89473),h=(i(5841),i(17262),i(42921),i(23897),i(92542)),p=i(39396),_=e([d,c]);[d,c]=_.then?(await _)():_;class u extends r.WF{async showDialog(e){this._params=e,this._groupAddresses=e.groupAddresses??[],this.knx=e.knx,this._selected=e.initialSelection??this._selected,this._open=!0}closeDialog(e){return this._dialogClosed(),!0}_cancel(){this._selected=void 0,this._params?.onClose&&this._params.onClose(void 0),this._dialogClosed()}_confirm(){this._params?.onClose&&this._params.onClose(this._selected),this._dialogClosed()}_itemKeydown(e){if("Enter"===e.key){e.preventDefault();const t=e.currentTarget.getAttribute("value");t&&(this._selected=t,this._confirm())}}_onDoubleClick(e){const t=e.currentTarget.getAttribute("value");this._selected=t??void 0,this._selected&&this._confirm()}_onSelect(e){const t=e.currentTarget.getAttribute("value");this._selected=t??void 0}_onFilterChanged(e){this._filter=e.detail?.value??""}_dialogClosed(){this._open=!1,this._params=void 0,this._filter="",this._selected=void 0,(0,h.r)(this,"dialog-closed",{dialog:this.localName})}_renderGroup(e){return r.qy`
      <div class="group-section">
        <div class="group-title" style="--group-depth: ${e.depth}">${e.title}</div>
        ${e.items.length>0?r.qy`<ha-md-list>
              ${e.items.map((e=>{const t=this._selected===e.address;return r.qy`<ha-md-list-item
                  interactive
                  type="button"
                  value=${e.address}
                  @click=${this._onSelect}
                  @dblclick=${this._onDoubleClick}
                  @keydown=${this._itemKeydown}
                >
                  <div class=${(0,n.H)({"ga-row":!0,selected:t})} slot="headline">
                    <div class="ga-address">${e.address}</div>
                    <div class="ga-name">${e.name??""}</div>
                  </div>
                </ha-md-list-item>`}))}
            </ha-md-list>`:r.s6}
        ${e.childGroups.map((e=>this._renderGroup(e)))}
      </div>
    `}render(){if(!this._params||!this.hass)return r.s6;const e=!this.knx.projectData?.group_ranges,t=this._groupAddresses?.length>0,i=t?this._groupItems(this._filter,this._groupAddresses,this.knx.projectData):[],o=i.length>0;return r.qy`<ha-wa-dialog
      .hass=${this.hass}
      .open=${this._open}
      width=${this._params.width??"medium"}
      .headerTitle=${this._params.title}
      @closed=${this._dialogClosed}
    >
      <div class="dialog-body">
        <search-input
          ?autofocus=${!0}
          .hass=${this.hass}
          .filter=${this._filter}
          @value-changed=${this._onFilterChanged}
          .label=${this.hass.localize("ui.common.search")}
        ></search-input>

        <div class="ga-list-container">
          ${e||!t?r.qy`<div class="empty-state">
                ${this.hass.localize("component.knx.config_panel.entities.create._.knx.knx_group_address.group_address_none_for_dpt")}
              </div>`:o?i.map((e=>this._renderGroup(e))):r.qy`<div class="empty-state">
                  ${this.hass.localize("component.knx.config_panel.entities.create._.knx.knx_group_address.group_address_none_for_filter")}
                </div>`}
        </div>
      </div>

      <ha-dialog-footer slot="footer">
        <ha-button slot="secondaryAction" appearance="plain" @click=${this._cancel}>
          ${this.hass.localize("ui.common.cancel")}
        </ha-button>
        <ha-button slot="primaryAction" @click=${this._confirm} .disabled=${!this._selected}>
          ${this.hass.localize("ui.common.ok")}
        </ha-button>
      </ha-dialog-footer>
    </ha-wa-dialog>`}static get styles(){return[p.nA,r.AH`
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

        ha-md-list {
          padding: 0;
        }

        .ga-list-container {
          flex: 1 1 auto;
          min-height: 0;
          overflow: auto;
          border: 1px solid var(--divider-color);
          border-radius: 4px;
          padding: 0;
        }

        .group-title {
          position: sticky;
          top: calc(var(--group-title-height, 40px) * min(1, var(--group-depth, 0)));
          z-index: calc(10 - var(--group-depth, 0));
          height: var(--group-title-height, 40px);
          box-sizing: border-box;
          display: flex;
          align-items: center;
          font-weight: 600;
          padding: 6px 8px;
          padding-left: calc(8px + var(--group-depth, 0) * 8px);
          color: var(--primary-text-color);
          background: var(--primary-background-color);
          border-bottom: 1px solid var(--divider-color);
        }

        .empty-state {
          padding: 12px;
          color: var(--secondary-text-color);
          font-style: italic;
        }

        .ga-row {
          display: grid;
          grid-template-columns: 10ch minmax(0, 1fr);
          align-items: center;
          gap: var(--ha-space-2, 8px);
          padding: 6px 8px;
          border-radius: 4px;
        }

        .ga-row.selected {
          background-color: rgba(var(--rgb-primary-color), 0.08);
          outline: 2px solid rgba(var(--rgb-accent-color), 0.12);
        }

        .ga-address {
          font-family:
            ui-monospace, SFMono-Regular, Menlo, Monaco, "Roboto Mono", "Courier New", monospace;
          width: 100%;
          color: var(--secondary-text-color);
          white-space: nowrap;
        }

        .ga-name {
          font-weight: 500;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
          min-width: 0;
        }
      `]}constructor(...e){super(...e),this._open=!1,this._groupAddresses=[],this._filter="",this._groupItems=(0,a.A)(((e,t,i)=>{const o=e.trim().toLowerCase();if(!i||!i.group_ranges)return[];const s=t.filter((e=>{if(!o)return!0;const t=e.address??"",i=e.name??"";return t.toLowerCase().includes(o)||i.toLowerCase().includes(o)})),a=(e,t=0)=>{const i=[];return Object.entries(e).forEach((([e,o])=>{const r=o.group_addresses??[],l=s.filter((e=>r.includes(e.address))),n=o.group_ranges?a(o.group_ranges,t+1):[];(l.length>0||n.length>0)&&i.push({title:`${e} ${o.name}`.trim(),items:l.sort(((e,t)=>e.raw_address-t.raw_address)),depth:t,childGroups:n})})),i};return a(i.group_ranges)}))}}(0,s.__decorate)([(0,l.MZ)({attribute:!1})],u.prototype,"hass",void 0),(0,s.__decorate)([(0,l.MZ)({attribute:!1})],u.prototype,"knx",void 0),(0,s.__decorate)([(0,l.wk)()],u.prototype,"_open",void 0),(0,s.__decorate)([(0,l.wk)()],u.prototype,"_params",void 0),(0,s.__decorate)([(0,l.wk)()],u.prototype,"_groupAddresses",void 0),(0,s.__decorate)([(0,l.wk)()],u.prototype,"_selected",void 0),(0,s.__decorate)([(0,l.wk)()],u.prototype,"_filter",void 0),u=(0,s.__decorate)([(0,l.EM)("knx-ga-select-dialog")],u),o()}catch(u){o(u)}}))}};
//# sourceMappingURL=2154.b0f49fc331c9783a.js.map
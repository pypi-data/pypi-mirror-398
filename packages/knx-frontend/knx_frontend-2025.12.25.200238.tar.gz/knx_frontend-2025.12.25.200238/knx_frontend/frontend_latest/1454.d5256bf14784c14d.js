export const __webpack_id__="1454";export const __webpack_ids__=["1454"];export const __webpack_modules__={2173:function(t,e,a){a.a(t,(async function(t,i){try{a.r(e),a.d(e,{HaFormOptionalActions:()=>_});var o=a(62826),s=a(96196),c=a(77845),d=a(22786),h=a(55124),n=a(89473),l=(a(56565),a(60961),a(91120),t([n]));n=(l.then?(await l)():l)[0];const p="M19,13H13V19H11V13H5V11H11V5H13V11H19V13Z",r=[];class _ extends s.WF{async focus(){await this.updateComplete,this.renderRoot.querySelector("ha-form")?.focus()}updated(t){if(super.updated(t),t.has("data")){const t=this._displayActions??r,e=this._hiddenActions(this.schema.schema,t);this._displayActions=[...t,...e.filter((t=>t in this.data))]}}render(){const t=this._displayActions??r,e=this._displaySchema(this.schema.schema,this._displayActions??[]),a=this._hiddenActions(this.schema.schema,t),i=new Map(this.computeLabel?this.schema.schema.map((t=>[t.name,t])):[]);return s.qy`
      ${e.length>0?s.qy`
            <ha-form
              .hass=${this.hass}
              .data=${this.data}
              .schema=${e}
              .disabled=${this.disabled}
              .computeLabel=${this.computeLabel}
              .computeHelper=${this.computeHelper}
              .localizeValue=${this.localizeValue}
            ></ha-form>
          `:s.s6}
      ${a.length>0?s.qy`
            <ha-button-menu
              @action=${this._handleAddAction}
              fixed
              @closed=${h.d}
            >
              <ha-button slot="trigger" appearance="filled" size="small">
                <ha-svg-icon .path=${p} slot="start"></ha-svg-icon>
                ${this.localize?.("ui.components.form-optional-actions.add")||"Add interaction"}
              </ha-button>
              ${a.map((t=>{const e=i.get(t);return s.qy`
                  <ha-list-item>
                    ${this.computeLabel&&e?this.computeLabel(e):t}
                  </ha-list-item>
                `}))}
            </ha-button-menu>
          `:s.s6}
    `}_handleAddAction(t){const e=this._hiddenActions(this.schema.schema,this._displayActions??r)[t.detail.index];this._displayActions=[...this._displayActions??[],e]}constructor(...t){super(...t),this.disabled=!1,this._hiddenActions=(0,d.A)(((t,e)=>t.map((t=>t.name)).filter((t=>!e.includes(t))))),this._displaySchema=(0,d.A)(((t,e)=>t.filter((t=>e.includes(t.name)))))}}_.styles=s.AH`
    :host {
      display: flex !important;
      flex-direction: column;
      gap: var(--ha-space-6);
    }
    :host ha-form {
      display: block;
    }
  `,(0,o.__decorate)([(0,c.MZ)({attribute:!1})],_.prototype,"localize",void 0),(0,o.__decorate)([(0,c.MZ)({attribute:!1})],_.prototype,"hass",void 0),(0,o.__decorate)([(0,c.MZ)({attribute:!1})],_.prototype,"data",void 0),(0,o.__decorate)([(0,c.MZ)({attribute:!1})],_.prototype,"schema",void 0),(0,o.__decorate)([(0,c.MZ)({type:Boolean})],_.prototype,"disabled",void 0),(0,o.__decorate)([(0,c.MZ)({attribute:!1})],_.prototype,"computeLabel",void 0),(0,o.__decorate)([(0,c.MZ)({attribute:!1})],_.prototype,"computeHelper",void 0),(0,o.__decorate)([(0,c.MZ)({attribute:!1})],_.prototype,"localizeValue",void 0),(0,o.__decorate)([(0,c.wk)()],_.prototype,"_displayActions",void 0),_=(0,o.__decorate)([(0,c.EM)("ha-form-optional_actions")],_),i()}catch(p){i(p)}}))}};
//# sourceMappingURL=1454.d5256bf14784c14d.js.map
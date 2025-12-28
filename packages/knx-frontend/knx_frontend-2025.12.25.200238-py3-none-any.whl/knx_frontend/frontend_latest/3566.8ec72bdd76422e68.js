export const __webpack_id__="3566";export const __webpack_ids__=["3566"];export const __webpack_modules__={60029:function(t,a,i){i.a(t,(async function(t,e){try{i.r(a),i.d(a,{HaImagecropperDialog:()=>m});var o=i(62826),r=i(23318),s=i.n(r),p=i(32609),c=i(96196),n=i(77845),h=i(94333),_=i(89473),l=(i(95637),i(39396)),d=t([_]);_=(d.then?(await d)():d)[0];class m extends c.WF{showDialog(t){this._params=t,this._open=!0}closeDialog(){this._open=!1,this._params=void 0,this._cropper?.destroy(),this._cropper=void 0,this._isTargetAspectRatio=!1}updated(t){t.has("_params")&&this._params&&(this._cropper?this._cropper.replace(URL.createObjectURL(this._params.file)):(this._image.src=URL.createObjectURL(this._params.file),this._cropper=new(s())(this._image,{aspectRatio:this._params.options.aspectRatio,viewMode:1,dragMode:"move",minCropBoxWidth:50,ready:()=>{this._isTargetAspectRatio=this._checkMatchAspectRatio(),URL.revokeObjectURL(this._image.src)}})))}_checkMatchAspectRatio(){const t=this._params?.options.aspectRatio;if(!t)return!0;const a=this._cropper.getImageData();if(a.aspectRatio===t)return!0;if(a.naturalWidth>a.naturalHeight){const i=a.naturalWidth/t;return Math.abs(i-a.naturalHeight)<=1}const i=a.naturalHeight*t;return Math.abs(i-a.naturalWidth)<=1}render(){return c.qy`<ha-dialog
      @closed=${this.closeDialog}
      scrimClickAction
      escapeKeyAction
      .open=${this._open}
    >
      <div
        class="container ${(0,h.H)({round:Boolean(this._params?.options.round)})}"
      >
        <img alt=${this.hass.localize("ui.dialogs.image_cropper.crop_image")} />
      </div>
      <ha-button
        appearance="plain"
        slot="primaryAction"
        @click=${this.closeDialog}
      >
        ${this.hass.localize("ui.common.cancel")}
      </ha-button>
      ${this._isTargetAspectRatio?c.qy`<ha-button
            appearance="plain"
            slot="primaryAction"
            @click=${this._useOriginal}
          >
            ${this.hass.localize("ui.dialogs.image_cropper.use_original")}
          </ha-button>`:c.s6}

      <ha-button slot="primaryAction" @click=${this._cropImage}>
        ${this.hass.localize("ui.dialogs.image_cropper.crop")}
      </ha-button>
    </ha-dialog>`}_cropImage(){this._cropper.getCroppedCanvas().toBlob((t=>{if(!t)return;const a=new File([t],this._params.file.name,{type:this._params.options.type||this._params.file.type});this._params.croppedCallback(a),this.closeDialog()}),this._params.options.type||this._params.file.type,this._params.options.quality)}_useOriginal(){this._params.croppedCallback(this._params.file),this.closeDialog()}static get styles(){return[l.nA,c.AH`
        ${(0,c.iz)(p)}
        .container {
          max-width: 640px;
        }
        img {
          max-width: 100%;
        }
        .container.round .cropper-view-box,
        .container.round .cropper-face {
          border-radius: var(--ha-border-radius-circle);
        }
        .cropper-line,
        .cropper-point,
        .cropper-point.point-se::before {
          background-color: var(--primary-color);
        }
      `]}constructor(...t){super(...t),this._open=!1}}(0,o.__decorate)([(0,n.MZ)({attribute:!1})],m.prototype,"hass",void 0),(0,o.__decorate)([(0,n.wk)()],m.prototype,"_params",void 0),(0,o.__decorate)([(0,n.wk)()],m.prototype,"_open",void 0),(0,o.__decorate)([(0,n.P)("img",!0)],m.prototype,"_image",void 0),(0,o.__decorate)([(0,n.wk)()],m.prototype,"_isTargetAspectRatio",void 0),m=(0,o.__decorate)([(0,n.EM)("image-cropper-dialog")],m),e()}catch(m){e(m)}}))}};
//# sourceMappingURL=3566.8ec72bdd76422e68.js.map
import { f as fetchCloudStorageConnectionsInterfaces, c as createCloudStorageConnectionApi, d as deleteCloudStorageConnectionApi } from "./api-c1bad5ca.js";
import { d as defineComponent, r as ref, m as watch, l as computed, c as openBlock, e as createElementBlock, p as createBaseVNode, a8 as withDirectives, a9 as vModelText, ak as vModelSelect, F as Fragment, q as renderList, t as toDisplayString, i as createCommentVNode, al as vModelDynamic, s as normalizeClass, am as vModelCheckbox, v as withModifiers, n as onMounted, g as createTextVNode, f as createVNode, w as withCtx, u as unref, z as ElMessage, an as ElDialog, ao as ElButton, _ as _export_sfc } from "./index-5429bbf8.js";
const _hoisted_1$1 = { class: "form-grid" };
const _hoisted_2$1 = { class: "form-field" };
const _hoisted_3$1 = { class: "form-field" };
const _hoisted_4$1 = { class: "form-field" };
const _hoisted_5$1 = ["value"];
const _hoisted_6$1 = { class: "form-field" };
const _hoisted_7$1 = ["required"];
const _hoisted_8$1 = {
  key: 0,
  class: "form-field"
};
const _hoisted_9$1 = ["required"];
const _hoisted_10$1 = {
  key: 1,
  class: "form-field"
};
const _hoisted_11$1 = { class: "password-field" };
const _hoisted_12$1 = ["type", "required"];
const _hoisted_13$1 = {
  key: 2,
  class: "form-field"
};
const _hoisted_14$1 = ["required"];
const _hoisted_15$1 = { class: "form-field" };
const _hoisted_16$1 = { class: "checkbox-container" };
const _hoisted_17$1 = { class: "form-field" };
const _hoisted_18$1 = ["required"];
const _hoisted_19$1 = {
  key: 0,
  class: "form-field"
};
const _hoisted_20$1 = { class: "password-field" };
const _hoisted_21$1 = ["type", "required"];
const _hoisted_22 = { class: "form-field" };
const _hoisted_23 = ["required"];
const _hoisted_24 = { class: "form-field" };
const _hoisted_25 = ["required"];
const _hoisted_26 = { class: "form-field" };
const _hoisted_27 = { class: "password-field" };
const _hoisted_28 = ["type", "required"];
const _hoisted_29 = { class: "form-field" };
const _hoisted_30 = { class: "form-field" };
const _hoisted_31 = { class: "checkbox-container" };
const _hoisted_32 = { class: "form-actions" };
const _hoisted_33 = ["disabled"];
const _sfc_main$1 = /* @__PURE__ */ defineComponent({
  __name: "CloudConnectionSettings",
  props: {
    initialConnection: {},
    isSubmitting: { type: Boolean }
  },
  emits: ["submit", "cancel"],
  setup(__props, { emit: __emit }) {
    const props = __props;
    const emit = __emit;
    const authMethodsByStorageType = {
      s3: [
        { value: "access_key", label: "Access Key" },
        { value: "iam_role", label: "IAM Role" },
        { value: "aws-cli", label: "AWS CLI" },
        { value: "auto", label: "Auto" }
      ],
      adls: [
        { value: "access_key", label: "Access Key" },
        { value: "service_principal", label: "Service Principal" },
        { value: "managed_identity", label: "Managed Identity" },
        { value: "sas_token", label: "SAS Token" },
        { value: "auto", label: "Auto" }
      ]
    };
    const defaultConnection = () => ({
      connectionName: "",
      storageType: "s3",
      authMethod: "access_key",
      verifySsl: true,
      awsAllowUnsafeHtml: false
    });
    const connection = ref(
      props.initialConnection ? { ...props.initialConnection } : defaultConnection()
    );
    watch(
      () => props.initialConnection,
      (newVal) => {
        if (newVal) {
          connection.value = { ...newVal };
        }
      }
    );
    const showAwsSecret = ref(false);
    const showAzureKey = ref(false);
    const showAzureSecret = ref(false);
    const availableAuthMethods = computed(() => {
      const cloudStorageType = connection.value.storageType;
      return authMethodsByStorageType[cloudStorageType] || [];
    });
    watch(
      () => connection.value.storageType,
      (newStorageType) => {
        const methods = authMethodsByStorageType[newStorageType];
        if (methods && methods.length > 0) {
          const currentMethodAvailable = methods.some((m) => m.value === connection.value.authMethod);
          if (!currentMethodAvailable) {
            connection.value.authMethod = methods[0].value;
          }
        }
      }
    );
    const isValid = computed(() => {
      const baseValid = !!connection.value.connectionName && !!connection.value.storageType && !!connection.value.authMethod;
      if (!baseValid)
        return false;
      if (connection.value.storageType === "s3") {
        if (!connection.value.awsRegion)
          return false;
        if (connection.value.authMethod === "access_key") {
          return !!connection.value.awsAccessKeyId && !!connection.value.awsSecretAccessKey;
        } else if (connection.value.authMethod === "iam_role") {
          return !!connection.value.awsRoleArn;
        }
      }
      if (connection.value.storageType === "adls") {
        if (!connection.value.azureAccountName)
          return false;
        if (connection.value.authMethod === "access_key") {
          return !!connection.value.azureAccountKey;
        } else if (connection.value.authMethod === "service_principal") {
          return !!connection.value.azureTenantId && !!connection.value.azureClientId && !!connection.value.azureClientSecret;
        }
      }
      return true;
    });
    const submitButtonText = computed(() => {
      if (props.isSubmitting) {
        return "Saving...";
      }
      return props.initialConnection ? "Update Connection" : "Create Connection";
    });
    const submitForm = () => {
      if (isValid.value) {
        emit("submit", connection.value);
      }
    };
    return (_ctx, _cache) => {
      return openBlock(), createElementBlock("form", {
        class: "form",
        onSubmit: withModifiers(submitForm, ["prevent"])
      }, [
        createBaseVNode("div", _hoisted_1$1, [
          createBaseVNode("div", _hoisted_2$1, [
            _cache[19] || (_cache[19] = createBaseVNode("label", {
              for: "connection-name",
              class: "form-label"
            }, "Connection Name", -1)),
            withDirectives(createBaseVNode("input", {
              id: "connection-name",
              "onUpdate:modelValue": _cache[0] || (_cache[0] = ($event) => connection.value.connectionName = $event),
              type: "text",
              class: "form-input",
              placeholder: "my_cloud_storage",
              required: ""
            }, null, 512), [
              [vModelText, connection.value.connectionName]
            ])
          ]),
          createBaseVNode("div", _hoisted_3$1, [
            _cache[21] || (_cache[21] = createBaseVNode("label", {
              for: "storage-type",
              class: "form-label"
            }, "Storage Type", -1)),
            withDirectives(createBaseVNode("select", {
              id: "storage-type",
              "onUpdate:modelValue": _cache[1] || (_cache[1] = ($event) => connection.value.storageType = $event),
              class: "form-input",
              required: ""
            }, _cache[20] || (_cache[20] = [
              createBaseVNode("option", { value: "s3" }, "AWS S3", -1)
            ]), 512), [
              [vModelSelect, connection.value.storageType]
            ])
          ]),
          createBaseVNode("div", _hoisted_4$1, [
            _cache[22] || (_cache[22] = createBaseVNode("label", {
              for: "auth-method",
              class: "form-label"
            }, "Authentication Method", -1)),
            withDirectives(createBaseVNode("select", {
              id: "auth-method",
              "onUpdate:modelValue": _cache[2] || (_cache[2] = ($event) => connection.value.authMethod = $event),
              class: "form-input",
              required: ""
            }, [
              (openBlock(true), createElementBlock(Fragment, null, renderList(availableAuthMethods.value, (method) => {
                return openBlock(), createElementBlock("option", {
                  key: method.value,
                  value: method.value
                }, toDisplayString(method.label), 9, _hoisted_5$1);
              }), 128))
            ], 512), [
              [vModelSelect, connection.value.authMethod]
            ])
          ]),
          connection.value.storageType === "s3" ? (openBlock(), createElementBlock(Fragment, { key: 0 }, [
            createBaseVNode("div", _hoisted_6$1, [
              _cache[23] || (_cache[23] = createBaseVNode("label", {
                for: "aws-region",
                class: "form-label"
              }, "AWS Region", -1)),
              withDirectives(createBaseVNode("input", {
                id: "aws-region",
                "onUpdate:modelValue": _cache[3] || (_cache[3] = ($event) => connection.value.awsRegion = $event),
                type: "text",
                class: "form-input",
                placeholder: "us-east-1",
                required: connection.value.storageType === "s3"
              }, null, 8, _hoisted_7$1), [
                [vModelText, connection.value.awsRegion]
              ])
            ]),
            connection.value.authMethod === "access_key" ? (openBlock(), createElementBlock("div", _hoisted_8$1, [
              _cache[24] || (_cache[24] = createBaseVNode("label", {
                for: "aws-access-key-id",
                class: "form-label"
              }, "AWS Access Key ID", -1)),
              withDirectives(createBaseVNode("input", {
                id: "aws-access-key-id",
                "onUpdate:modelValue": _cache[4] || (_cache[4] = ($event) => connection.value.awsAccessKeyId = $event),
                type: "text",
                class: "form-input",
                placeholder: "AKIAIOSFODNN7EXAMPLE",
                required: connection.value.authMethod === "access_key"
              }, null, 8, _hoisted_9$1), [
                [vModelText, connection.value.awsAccessKeyId]
              ])
            ])) : createCommentVNode("", true),
            connection.value.authMethod === "access_key" ? (openBlock(), createElementBlock("div", _hoisted_10$1, [
              _cache[25] || (_cache[25] = createBaseVNode("label", {
                for: "aws-secret-access-key",
                class: "form-label"
              }, "AWS Secret Access Key", -1)),
              createBaseVNode("div", _hoisted_11$1, [
                withDirectives(createBaseVNode("input", {
                  id: "aws-secret-access-key",
                  "onUpdate:modelValue": _cache[5] || (_cache[5] = ($event) => connection.value.awsSecretAccessKey = $event),
                  type: showAwsSecret.value ? "text" : "password",
                  class: "form-input",
                  placeholder: "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                  required: connection.value.authMethod === "access_key"
                }, null, 8, _hoisted_12$1), [
                  [vModelDynamic, connection.value.awsSecretAccessKey]
                ]),
                createBaseVNode("button", {
                  type: "button",
                  class: "toggle-visibility",
                  "aria-label": "Toggle AWS secret visibility",
                  onClick: _cache[6] || (_cache[6] = ($event) => showAwsSecret.value = !showAwsSecret.value)
                }, [
                  createBaseVNode("i", {
                    class: normalizeClass(showAwsSecret.value ? "fa-solid fa-eye-slash" : "fa-solid fa-eye")
                  }, null, 2)
                ])
              ])
            ])) : createCommentVNode("", true),
            connection.value.authMethod === "iam_role" ? (openBlock(), createElementBlock("div", _hoisted_13$1, [
              _cache[26] || (_cache[26] = createBaseVNode("label", {
                for: "aws-role-arn",
                class: "form-label"
              }, "AWS Role ARN", -1)),
              withDirectives(createBaseVNode("input", {
                id: "aws-role-arn",
                "onUpdate:modelValue": _cache[7] || (_cache[7] = ($event) => connection.value.awsRoleArn = $event),
                type: "text",
                class: "form-input",
                placeholder: "arn:aws:iam::123456789012:role/MyRole",
                required: connection.value.authMethod === "iam_role"
              }, null, 8, _hoisted_14$1), [
                [vModelText, connection.value.awsRoleArn]
              ])
            ])) : createCommentVNode("", true),
            createBaseVNode("div", _hoisted_15$1, [
              createBaseVNode("div", _hoisted_16$1, [
                withDirectives(createBaseVNode("input", {
                  id: "aws-allow-unsafe-html",
                  "onUpdate:modelValue": _cache[8] || (_cache[8] = ($event) => connection.value.awsAllowUnsafeHtml = $event),
                  type: "checkbox",
                  class: "checkbox-input"
                }, null, 512), [
                  [vModelCheckbox, connection.value.awsAllowUnsafeHtml]
                ]),
                _cache[27] || (_cache[27] = createBaseVNode("label", {
                  for: "aws-allow-unsafe-html",
                  class: "form-label"
                }, "Allow Unsafe HTML", -1))
              ])
            ])
          ], 64)) : createCommentVNode("", true),
          connection.value.storageType === "adls" ? (openBlock(), createElementBlock(Fragment, { key: 1 }, [
            createBaseVNode("div", _hoisted_17$1, [
              _cache[28] || (_cache[28] = createBaseVNode("label", {
                for: "azure-account-name",
                class: "form-label"
              }, "Azure Account Name", -1)),
              withDirectives(createBaseVNode("input", {
                id: "azure-account-name",
                "onUpdate:modelValue": _cache[9] || (_cache[9] = ($event) => connection.value.azureAccountName = $event),
                type: "text",
                class: "form-input",
                placeholder: "mystorageaccount",
                required: connection.value.storageType === "adls"
              }, null, 8, _hoisted_18$1), [
                [vModelText, connection.value.azureAccountName]
              ])
            ]),
            connection.value.authMethod === "access_key" ? (openBlock(), createElementBlock("div", _hoisted_19$1, [
              _cache[29] || (_cache[29] = createBaseVNode("label", {
                for: "azure-account-key",
                class: "form-label"
              }, "Azure Account Key", -1)),
              createBaseVNode("div", _hoisted_20$1, [
                withDirectives(createBaseVNode("input", {
                  id: "azure-account-key",
                  "onUpdate:modelValue": _cache[10] || (_cache[10] = ($event) => connection.value.azureAccountKey = $event),
                  type: showAzureKey.value ? "text" : "password",
                  class: "form-input",
                  placeholder: "Account key",
                  required: connection.value.authMethod === "access_key"
                }, null, 8, _hoisted_21$1), [
                  [vModelDynamic, connection.value.azureAccountKey]
                ]),
                createBaseVNode("button", {
                  type: "button",
                  class: "toggle-visibility",
                  "aria-label": "Toggle Azure key visibility",
                  onClick: _cache[11] || (_cache[11] = ($event) => showAzureKey.value = !showAzureKey.value)
                }, [
                  createBaseVNode("i", {
                    class: normalizeClass(showAzureKey.value ? "fa-solid fa-eye-slash" : "fa-solid fa-eye")
                  }, null, 2)
                ])
              ])
            ])) : createCommentVNode("", true),
            connection.value.authMethod === "service_principal" ? (openBlock(), createElementBlock(Fragment, { key: 1 }, [
              createBaseVNode("div", _hoisted_22, [
                _cache[30] || (_cache[30] = createBaseVNode("label", {
                  for: "azure-tenant-id",
                  class: "form-label"
                }, "Azure Tenant ID", -1)),
                withDirectives(createBaseVNode("input", {
                  id: "azure-tenant-id",
                  "onUpdate:modelValue": _cache[12] || (_cache[12] = ($event) => connection.value.azureTenantId = $event),
                  type: "text",
                  class: "form-input",
                  placeholder: "12345678-1234-1234-1234-123456789012",
                  required: connection.value.authMethod === "service_principal"
                }, null, 8, _hoisted_23), [
                  [vModelText, connection.value.azureTenantId]
                ])
              ]),
              createBaseVNode("div", _hoisted_24, [
                _cache[31] || (_cache[31] = createBaseVNode("label", {
                  for: "azure-client-id",
                  class: "form-label"
                }, "Azure Client ID", -1)),
                withDirectives(createBaseVNode("input", {
                  id: "azure-client-id",
                  "onUpdate:modelValue": _cache[13] || (_cache[13] = ($event) => connection.value.azureClientId = $event),
                  type: "text",
                  class: "form-input",
                  placeholder: "12345678-1234-1234-1234-123456789012",
                  required: connection.value.authMethod === "service_principal"
                }, null, 8, _hoisted_25), [
                  [vModelText, connection.value.azureClientId]
                ])
              ]),
              createBaseVNode("div", _hoisted_26, [
                _cache[32] || (_cache[32] = createBaseVNode("label", {
                  for: "azure-client-secret",
                  class: "form-label"
                }, "Azure Client Secret", -1)),
                createBaseVNode("div", _hoisted_27, [
                  withDirectives(createBaseVNode("input", {
                    id: "azure-client-secret",
                    "onUpdate:modelValue": _cache[14] || (_cache[14] = ($event) => connection.value.azureClientSecret = $event),
                    type: showAzureSecret.value ? "text" : "password",
                    class: "form-input",
                    placeholder: "Client secret",
                    required: connection.value.authMethod === "service_principal"
                  }, null, 8, _hoisted_28), [
                    [vModelDynamic, connection.value.azureClientSecret]
                  ]),
                  createBaseVNode("button", {
                    type: "button",
                    class: "toggle-visibility",
                    "aria-label": "Toggle Azure secret visibility",
                    onClick: _cache[15] || (_cache[15] = ($event) => showAzureSecret.value = !showAzureSecret.value)
                  }, [
                    createBaseVNode("i", {
                      class: normalizeClass(showAzureSecret.value ? "fa-solid fa-eye-slash" : "fa-solid fa-eye")
                    }, null, 2)
                  ])
                ])
              ])
            ], 64)) : createCommentVNode("", true)
          ], 64)) : createCommentVNode("", true),
          createBaseVNode("div", _hoisted_29, [
            _cache[33] || (_cache[33] = createBaseVNode("label", {
              for: "endpoint-url",
              class: "form-label"
            }, "Custom Endpoint URL (Optional)", -1)),
            withDirectives(createBaseVNode("input", {
              id: "endpoint-url",
              "onUpdate:modelValue": _cache[16] || (_cache[16] = ($event) => connection.value.endpointUrl = $event),
              type: "text",
              class: "form-input",
              placeholder: "https://custom-endpoint.example.com"
            }, null, 512), [
              [vModelText, connection.value.endpointUrl]
            ])
          ]),
          createBaseVNode("div", _hoisted_30, [
            createBaseVNode("div", _hoisted_31, [
              withDirectives(createBaseVNode("input", {
                id: "verify-ssl",
                "onUpdate:modelValue": _cache[17] || (_cache[17] = ($event) => connection.value.verifySsl = $event),
                type: "checkbox",
                class: "checkbox-input"
              }, null, 512), [
                [vModelCheckbox, connection.value.verifySsl]
              ]),
              _cache[34] || (_cache[34] = createBaseVNode("label", {
                for: "verify-ssl",
                class: "form-label"
              }, "Verify SSL", -1))
            ])
          ])
        ]),
        createBaseVNode("div", _hoisted_32, [
          createBaseVNode("button", {
            type: "button",
            class: "btn btn-secondary",
            onClick: _cache[18] || (_cache[18] = ($event) => _ctx.$emit("cancel"))
          }, "Cancel"),
          createBaseVNode("button", {
            type: "submit",
            class: "btn btn-primary",
            disabled: !isValid.value || _ctx.isSubmitting
          }, toDisplayString(submitButtonText.value), 9, _hoisted_33)
        ])
      ], 32);
    };
  }
});
const _hoisted_1 = { class: "cloud-connection-manager-container" };
const _hoisted_2 = { class: "card mb-3" };
const _hoisted_3 = { class: "card-header" };
const _hoisted_4 = { class: "card-title" };
const _hoisted_5 = { class: "card-content" };
const _hoisted_6 = {
  key: 0,
  class: "loading-state"
};
const _hoisted_7 = {
  key: 1,
  class: "empty-state"
};
const _hoisted_8 = {
  key: 2,
  class: "flex-col gap-2"
};
const _hoisted_9 = { class: "secret-info" };
const _hoisted_10 = { class: "secret-name" };
const _hoisted_11 = { class: "badge" };
const _hoisted_12 = { class: "badge auth-badge" };
const _hoisted_13 = { class: "connection-details" };
const _hoisted_14 = { key: 0 };
const _hoisted_15 = { key: 1 };
const _hoisted_16 = { key: 2 };
const _hoisted_17 = { key: 3 };
const _hoisted_18 = { class: "secret-actions" };
const _hoisted_19 = ["onClick"];
const _hoisted_20 = ["onClick"];
const _hoisted_21 = { class: "dialog-footer" };
const _sfc_main = /* @__PURE__ */ defineComponent({
  __name: "CloudConnectionManager",
  setup(__props) {
    const connectionInterfaces = ref([]);
    const isLoading = ref(true);
    const dialogVisible = ref(false);
    const deleteDialogVisible = ref(false);
    const isEditing = ref(false);
    const isSubmitting = ref(false);
    const isDeleting = ref(false);
    const connectionToDelete = ref("");
    const activeConnection = ref(void 0);
    const getStorageIcon = (storageType) => {
      switch (storageType) {
        case "s3":
          return "fa-brands fa-aws";
        case "adls":
          return "fa-brands fa-microsoft";
        default:
          return "fa-solid fa-cloud";
      }
    };
    const getStorageLabel = (storageType) => {
      switch (storageType) {
        case "s3":
          return "AWS S3";
        case "adls":
          return "Azure ADLS";
        default:
          return storageType.toUpperCase();
      }
    };
    const getAuthMethodLabel = (authMethod) => {
      switch (authMethod) {
        case "access_key":
          return "Access Key";
        case "iam_role":
          return "IAM Role";
        case "service_principal":
          return "Service Principal";
        case "managed_identity":
          return "Managed Identity";
        case "sas_token":
          return "SAS Token";
        case "aws-cli":
          return "AWS CLI";
        case "auto":
          return "Auto";
        default:
          return authMethod;
      }
    };
    const fetchConnections = async () => {
      isLoading.value = true;
      try {
        connectionInterfaces.value = await fetchCloudStorageConnectionsInterfaces();
      } catch (error) {
        console.error("Error fetching connections:", error);
        ElMessage.error("Failed to load cloud storage connections");
      } finally {
        isLoading.value = false;
      }
    };
    const showAddModal = () => {
      isEditing.value = false;
      activeConnection.value = void 0;
      dialogVisible.value = true;
    };
    const showEditModal = (connection) => {
      isEditing.value = true;
      activeConnection.value = {
        connectionName: connection.connectionName,
        storageType: connection.storageType,
        authMethod: connection.authMethod,
        // AWS fields
        awsRegion: connection.awsRegion || "",
        awsAccessKeyId: connection.awsAccessKeyId || "",
        awsSecretAccessKey: "",
        // Password is not returned from the API
        awsRoleArn: connection.awsRoleArn || "",
        awsAllowUnsafeHtml: connection.awsAllowUnsafeHtml,
        // Azure fields
        azureAccountName: connection.azureAccountName || "",
        azureAccountKey: "",
        // Password is not returned from the API
        azureTenantId: connection.azureTenantId || "",
        azureClientId: connection.azureClientId || "",
        azureClientSecret: "",
        // Password is not returned from the API
        // Common fields
        endpointUrl: connection.endpointUrl || "",
        verifySsl: connection.verifySsl
      };
      dialogVisible.value = true;
    };
    const showDeleteModal = (connectionName) => {
      connectionToDelete.value = connectionName;
      deleteDialogVisible.value = true;
    };
    const handleFormSubmit = async (connection) => {
      isSubmitting.value = true;
      try {
        await createCloudStorageConnectionApi(connection);
        await fetchConnections();
        dialogVisible.value = false;
        ElMessage.success(`Connection ${isEditing.value ? "updated" : "created"} successfully`);
      } catch (error) {
        ElMessage.error(
          `Failed to ${isEditing.value ? "update" : "create"} connection: ${error.message || "Unknown error"}`
        );
      } finally {
        isSubmitting.value = false;
      }
    };
    const handleDeleteConnection = async () => {
      if (!connectionToDelete.value)
        return;
      isDeleting.value = true;
      try {
        await deleteCloudStorageConnectionApi(connectionToDelete.value);
        await fetchConnections();
        deleteDialogVisible.value = false;
        ElMessage.success("Connection deleted successfully");
      } catch (error) {
        ElMessage.error("Failed to delete connection");
      } finally {
        isDeleting.value = false;
        connectionToDelete.value = "";
      }
    };
    const handleCloseDialog = (done) => {
      if (isSubmitting.value)
        return;
      done();
    };
    const handleCloseDeleteDialog = (done) => {
      if (isDeleting.value)
        return;
      done();
    };
    onMounted(() => {
      fetchConnections();
    });
    return (_ctx, _cache) => {
      return openBlock(), createElementBlock("div", _hoisted_1, [
        _cache[18] || (_cache[18] = createBaseVNode("div", { class: "mb-3" }, [
          createBaseVNode("h2", { class: "page-title" }, "Cloud Storage Connections"),
          createBaseVNode("p", { class: "description-text" }, " Cloud storage connections allow you to connect to your cloud storage services like AWS S3 and Azure Data Lake Storage. Create and manage your connections here to use them in your data workflows. ")
        ], -1)),
        createBaseVNode("div", _hoisted_2, [
          createBaseVNode("div", _hoisted_3, [
            createBaseVNode("h3", _hoisted_4, "Your Connections (" + toDisplayString(connectionInterfaces.value.length) + ")", 1),
            createBaseVNode("button", {
              class: "btn btn-primary",
              onClick: showAddModal
            }, _cache[4] || (_cache[4] = [
              createBaseVNode("i", { class: "fa-solid fa-plus" }, null, -1),
              createTextVNode(" Add Connection ")
            ]))
          ]),
          createBaseVNode("div", _hoisted_5, [
            _cache[11] || (_cache[11] = createBaseVNode("div", { class: "info-box mb-3" }, [
              createBaseVNode("i", { class: "fa-solid fa-info-circle" }),
              createBaseVNode("div", null, [
                createBaseVNode("p", null, [
                  createBaseVNode("strong", null, "What are cloud storage connections?")
                ]),
                createBaseVNode("p", null, " Cloud storage connections store the credentials and configuration needed to securely access your cloud storage services. Once set up, you can reuse these connections throughout your workflows without re-entering credentials. ")
              ])
            ], -1)),
            isLoading.value ? (openBlock(), createElementBlock("div", _hoisted_6, _cache[5] || (_cache[5] = [
              createBaseVNode("div", { class: "loading-spinner" }, null, -1),
              createBaseVNode("p", null, "Loading connections...", -1)
            ]))) : connectionInterfaces.value.length === 0 ? (openBlock(), createElementBlock("div", _hoisted_7, _cache[6] || (_cache[6] = [
              createBaseVNode("i", { class: "fa-solid fa-cloud" }, null, -1),
              createBaseVNode("p", null, "You haven't added any cloud storage connections yet", -1),
              createBaseVNode("p", { class: "hint-text" }, ' Click the "Add Connection" button to create your first cloud storage connection. ', -1)
            ]))) : (openBlock(), createElementBlock("div", _hoisted_8, [
              (openBlock(true), createElementBlock(Fragment, null, renderList(connectionInterfaces.value, (connection) => {
                return openBlock(), createElementBlock("div", {
                  key: connection.connectionName,
                  class: "secret-item"
                }, [
                  createBaseVNode("div", _hoisted_9, [
                    createBaseVNode("div", _hoisted_10, [
                      createBaseVNode("i", {
                        class: normalizeClass(getStorageIcon(connection.storageType))
                      }, null, 2),
                      createBaseVNode("span", null, toDisplayString(connection.connectionName), 1),
                      createBaseVNode("span", _hoisted_11, toDisplayString(getStorageLabel(connection.storageType)), 1),
                      createBaseVNode("span", _hoisted_12, toDisplayString(getAuthMethodLabel(connection.authMethod)), 1)
                    ]),
                    createBaseVNode("div", _hoisted_13, [
                      connection.storageType === "s3" && connection.awsRegion ? (openBlock(), createElementBlock("span", _hoisted_14, " Region: " + toDisplayString(connection.awsRegion), 1)) : connection.storageType === "adls" && connection.azureAccountName ? (openBlock(), createElementBlock("span", _hoisted_15, " Account: " + toDisplayString(connection.azureAccountName), 1)) : createCommentVNode("", true),
                      connection.endpointUrl ? (openBlock(), createElementBlock("span", _hoisted_16, _cache[7] || (_cache[7] = [
                        createBaseVNode("span", { class: "separator" }, "•", -1),
                        createTextVNode(" Custom endpoint ")
                      ]))) : createCommentVNode("", true),
                      !connection.verifySsl ? (openBlock(), createElementBlock("span", _hoisted_17, _cache[8] || (_cache[8] = [
                        createBaseVNode("span", { class: "separator" }, "•", -1),
                        createTextVNode(" SSL verification disabled ")
                      ]))) : createCommentVNode("", true)
                    ])
                  ]),
                  createBaseVNode("div", _hoisted_18, [
                    createBaseVNode("button", {
                      type: "button",
                      class: "btn btn-secondary",
                      onClick: ($event) => showEditModal(connection)
                    }, _cache[9] || (_cache[9] = [
                      createBaseVNode("i", { class: "fa-solid fa-edit" }, null, -1),
                      createBaseVNode("span", null, "Modify", -1)
                    ]), 8, _hoisted_19),
                    connection.connectionName ? (openBlock(), createElementBlock("button", {
                      key: 0,
                      type: "button",
                      class: "btn btn-danger",
                      onClick: ($event) => showDeleteModal(connection.connectionName)
                    }, _cache[10] || (_cache[10] = [
                      createBaseVNode("i", { class: "fa-solid fa-trash-alt" }, null, -1),
                      createBaseVNode("span", null, "Delete", -1)
                    ]), 8, _hoisted_20)) : createCommentVNode("", true)
                  ])
                ]);
              }), 128))
            ]))
          ])
        ]),
        createVNode(unref(ElDialog), {
          modelValue: dialogVisible.value,
          "onUpdate:modelValue": _cache[1] || (_cache[1] = ($event) => dialogVisible.value = $event),
          title: isEditing.value ? "Edit Cloud Storage Connection" : "Add Cloud Storage Connection",
          width: "600px",
          "before-close": handleCloseDialog
        }, {
          default: withCtx(() => [
            _cache[12] || (_cache[12] = createBaseVNode("div", { class: "modal-description mb-3" }, [
              createBaseVNode("p", null, " Configure your cloud storage connection details. Choose your storage provider and authentication method, then provide the required credentials. ")
            ], -1)),
            createVNode(_sfc_main$1, {
              "initial-connection": activeConnection.value,
              "is-submitting": isSubmitting.value,
              onSubmit: handleFormSubmit,
              onCancel: _cache[0] || (_cache[0] = ($event) => dialogVisible.value = false)
            }, null, 8, ["initial-connection", "is-submitting"])
          ]),
          _: 1,
          __: [12]
        }, 8, ["modelValue", "title"]),
        createVNode(unref(ElDialog), {
          modelValue: deleteDialogVisible.value,
          "onUpdate:modelValue": _cache[3] || (_cache[3] = ($event) => deleteDialogVisible.value = $event),
          title: "Delete Connection",
          width: "400px",
          "before-close": handleCloseDeleteDialog
        }, {
          footer: withCtx(() => [
            createBaseVNode("div", _hoisted_21, [
              createVNode(unref(ElButton), {
                onClick: _cache[2] || (_cache[2] = ($event) => deleteDialogVisible.value = false)
              }, {
                default: withCtx(() => _cache[15] || (_cache[15] = [
                  createTextVNode("Cancel")
                ])),
                _: 1,
                __: [15]
              }),
              createVNode(unref(ElButton), {
                type: "danger",
                loading: isDeleting.value,
                onClick: handleDeleteConnection
              }, {
                default: withCtx(() => _cache[16] || (_cache[16] = [
                  createTextVNode(" Delete ")
                ])),
                _: 1,
                __: [16]
              }, 8, ["loading"])
            ])
          ]),
          default: withCtx(() => [
            createBaseVNode("p", null, [
              _cache[13] || (_cache[13] = createTextVNode(" Are you sure you want to delete the connection ")),
              createBaseVNode("strong", null, toDisplayString(connectionToDelete.value), 1),
              _cache[14] || (_cache[14] = createTextVNode("? "))
            ]),
            _cache[17] || (_cache[17] = createBaseVNode("p", { class: "warning-text" }, " This action cannot be undone and may affect any processes using this connection. ", -1))
          ]),
          _: 1,
          __: [17]
        }, 8, ["modelValue"])
      ]);
    };
  }
});
const CloudConnectionManager_vue_vue_type_style_index_0_scoped_23359c71_lang = "";
const CloudConnectionManager = /* @__PURE__ */ _export_sfc(_sfc_main, [["__scopeId", "data-v-23359c71"]]);
export {
  CloudConnectionManager as default
};

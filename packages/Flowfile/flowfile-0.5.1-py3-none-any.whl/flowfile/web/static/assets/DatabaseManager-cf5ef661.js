import { f as fetchDatabaseConnectionsInterfaces, c as createDatabaseConnectionApi, d as deleteDatabaseConnectionApi } from "./api-cf1221f0.js";
import { d as defineComponent, r as ref, m as watch, l as computed, c as openBlock, e as createElementBlock, p as createBaseVNode, a8 as withDirectives, a9 as vModelText, ak as vModelSelect, al as vModelDynamic, s as normalizeClass, am as vModelCheckbox, t as toDisplayString, v as withModifiers, n as onMounted, g as createTextVNode, F as Fragment, q as renderList, f as createVNode, w as withCtx, u as unref, z as ElMessage, an as ElDialog, ao as ElButton, _ as _export_sfc } from "./index-5429bbf8.js";
const _hoisted_1$1 = { class: "form-grid" };
const _hoisted_2$1 = { class: "form-field" };
const _hoisted_3$1 = { class: "form-field" };
const _hoisted_4$1 = { class: "form-field" };
const _hoisted_5$1 = { class: "form-field" };
const _hoisted_6$1 = { class: "form-field" };
const _hoisted_7$1 = { class: "form-field" };
const _hoisted_8$1 = { class: "form-field" };
const _hoisted_9$1 = { class: "password-field" };
const _hoisted_10$1 = ["type"];
const _hoisted_11$1 = { class: "form-field" };
const _hoisted_12$1 = { class: "checkbox-container" };
const _hoisted_13$1 = { class: "form-actions" };
const _hoisted_14$1 = ["disabled"];
const _sfc_main$1 = /* @__PURE__ */ defineComponent({
  __name: "DatabaseConnectionSettings",
  props: {
    initialConnection: {},
    isSubmitting: { type: Boolean }
  },
  emits: ["submit", "cancel"],
  setup(__props, { emit: __emit }) {
    const props = __props;
    const emit = __emit;
    const defaultConnection = () => ({
      connectionName: "",
      databaseType: "postgresql",
      username: "",
      password: "",
      host: "",
      port: 5432,
      database: "",
      sslEnabled: false,
      url: ""
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
    const showPassword = ref(false);
    const isValid = computed(() => {
      return !!connection.value.connectionName && !!connection.value.username && !!connection.value.password && !!connection.value.host;
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
            _cache[10] || (_cache[10] = createBaseVNode("label", {
              for: "connection-name",
              class: "form-label"
            }, "Connection Name", -1)),
            withDirectives(createBaseVNode("input", {
              id: "connection-name",
              "onUpdate:modelValue": _cache[0] || (_cache[0] = ($event) => connection.value.connectionName = $event),
              type: "text",
              class: "form-input",
              placeholder: "my_postgres_db",
              required: ""
            }, null, 512), [
              [vModelText, connection.value.connectionName]
            ])
          ]),
          createBaseVNode("div", _hoisted_3$1, [
            _cache[12] || (_cache[12] = createBaseVNode("label", {
              for: "database-type",
              class: "form-label"
            }, "Database Type", -1)),
            withDirectives(createBaseVNode("select", {
              id: "database-type",
              "onUpdate:modelValue": _cache[1] || (_cache[1] = ($event) => connection.value.databaseType = $event),
              class: "form-input",
              required: ""
            }, _cache[11] || (_cache[11] = [
              createBaseVNode("option", { value: "postgresql" }, "PostgreSQL", -1)
            ]), 512), [
              [vModelSelect, connection.value.databaseType]
            ])
          ]),
          createBaseVNode("div", _hoisted_4$1, [
            _cache[13] || (_cache[13] = createBaseVNode("label", {
              for: "host",
              class: "form-label"
            }, "Host", -1)),
            withDirectives(createBaseVNode("input", {
              id: "host",
              "onUpdate:modelValue": _cache[2] || (_cache[2] = ($event) => connection.value.host = $event),
              type: "text",
              class: "form-input",
              placeholder: "localhost or IP address",
              required: ""
            }, null, 512), [
              [vModelText, connection.value.host]
            ])
          ]),
          createBaseVNode("div", _hoisted_5$1, [
            _cache[14] || (_cache[14] = createBaseVNode("label", {
              for: "port",
              class: "form-label"
            }, "Port", -1)),
            withDirectives(createBaseVNode("input", {
              id: "port",
              "onUpdate:modelValue": _cache[3] || (_cache[3] = ($event) => connection.value.port = $event),
              type: "number",
              class: "form-input",
              placeholder: "5432"
            }, null, 512), [
              [vModelText, connection.value.port]
            ])
          ]),
          createBaseVNode("div", _hoisted_6$1, [
            _cache[15] || (_cache[15] = createBaseVNode("label", {
              for: "database",
              class: "form-label"
            }, "Database", -1)),
            withDirectives(createBaseVNode("input", {
              id: "database",
              "onUpdate:modelValue": _cache[4] || (_cache[4] = ($event) => connection.value.database = $event),
              type: "text",
              class: "form-input",
              placeholder: "Database name"
            }, null, 512), [
              [vModelText, connection.value.database]
            ])
          ]),
          createBaseVNode("div", _hoisted_7$1, [
            _cache[16] || (_cache[16] = createBaseVNode("label", {
              for: "username",
              class: "form-label"
            }, "Username", -1)),
            withDirectives(createBaseVNode("input", {
              id: "username",
              "onUpdate:modelValue": _cache[5] || (_cache[5] = ($event) => connection.value.username = $event),
              type: "text",
              class: "form-input",
              placeholder: "Username",
              required: ""
            }, null, 512), [
              [vModelText, connection.value.username]
            ])
          ]),
          createBaseVNode("div", _hoisted_8$1, [
            _cache[17] || (_cache[17] = createBaseVNode("label", {
              for: "password",
              class: "form-label"
            }, "Password", -1)),
            createBaseVNode("div", _hoisted_9$1, [
              withDirectives(createBaseVNode("input", {
                id: "password",
                "onUpdate:modelValue": _cache[6] || (_cache[6] = ($event) => connection.value.password = $event),
                type: showPassword.value ? "text" : "password",
                class: "form-input",
                placeholder: "Password",
                required: ""
              }, null, 8, _hoisted_10$1), [
                [vModelDynamic, connection.value.password]
              ]),
              createBaseVNode("button", {
                type: "button",
                class: "toggle-visibility",
                "aria-label": "Toggle password visibility",
                onClick: _cache[7] || (_cache[7] = ($event) => showPassword.value = !showPassword.value)
              }, [
                createBaseVNode("i", {
                  class: normalizeClass(showPassword.value ? "fa-solid fa-eye-slash" : "fa-solid fa-eye")
                }, null, 2)
              ])
            ])
          ]),
          createBaseVNode("div", _hoisted_11$1, [
            createBaseVNode("div", _hoisted_12$1, [
              withDirectives(createBaseVNode("input", {
                id: "ssl-enabled",
                "onUpdate:modelValue": _cache[8] || (_cache[8] = ($event) => connection.value.sslEnabled = $event),
                type: "checkbox",
                class: "checkbox-input"
              }, null, 512), [
                [vModelCheckbox, connection.value.sslEnabled]
              ]),
              _cache[18] || (_cache[18] = createBaseVNode("label", {
                for: "ssl-enabled",
                class: "form-label"
              }, "Enable SSL", -1))
            ])
          ])
        ]),
        createBaseVNode("div", _hoisted_13$1, [
          createBaseVNode("button", {
            type: "button",
            class: "btn btn-secondary",
            onClick: _cache[9] || (_cache[9] = ($event) => _ctx.$emit("cancel"))
          }, "Cancel"),
          createBaseVNode("button", {
            type: "submit",
            class: "btn btn-primary",
            disabled: !isValid.value || _ctx.isSubmitting
          }, toDisplayString(submitButtonText.value), 9, _hoisted_14$1)
        ])
      ], 32);
    };
  }
});
const _hoisted_1 = { class: "database-manager-container" };
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
const _hoisted_12 = { class: "connection-details" };
const _hoisted_13 = { class: "secret-actions" };
const _hoisted_14 = ["onClick"];
const _hoisted_15 = ["onClick"];
const _hoisted_16 = { class: "dialog-footer" };
const _sfc_main = /* @__PURE__ */ defineComponent({
  __name: "DatabaseManager",
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
    const fetchConnections = async () => {
      isLoading.value = true;
      try {
        connectionInterfaces.value = await fetchDatabaseConnectionsInterfaces();
      } catch (error) {
        console.error("Error fetching connections:", error);
        ElMessage.error("Failed to load database connections");
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
        databaseType: connection.databaseType,
        username: connection.username,
        password: "",
        // Password is not returned from the API
        host: connection.host || "",
        port: connection.port || 5432,
        database: connection.database || "",
        sslEnabled: connection.sslEnabled,
        url: connection.url || ""
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
        await createDatabaseConnectionApi(connection);
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
        await deleteDatabaseConnectionApi(connectionToDelete.value);
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
          createBaseVNode("h2", { class: "page-title" }, "Database Connections"),
          createBaseVNode("p", { class: "description-text" }, " Database connections allow you to connect to your databases for reading and writing data. Create and manage your connections here to use them in your data workflows. ")
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
                  createBaseVNode("strong", null, "What are database connections?")
                ]),
                createBaseVNode("p", null, " Database connections store the credentials and configuration needed to securely access your databases. Once set up, you can reuse these connections throughout your workflows without re-entering credentials. ")
              ])
            ], -1)),
            isLoading.value ? (openBlock(), createElementBlock("div", _hoisted_6, _cache[5] || (_cache[5] = [
              createBaseVNode("div", { class: "loading-spinner" }, null, -1),
              createBaseVNode("p", null, "Loading connections...", -1)
            ]))) : connectionInterfaces.value.length === 0 ? (openBlock(), createElementBlock("div", _hoisted_7, _cache[6] || (_cache[6] = [
              createBaseVNode("i", { class: "fa-solid fa-database" }, null, -1),
              createBaseVNode("p", null, "You haven't added any database connections yet", -1),
              createBaseVNode("p", { class: "hint-text" }, ' Click the "Add Connection" button to create your first database connection. ', -1)
            ]))) : (openBlock(), createElementBlock("div", _hoisted_8, [
              (openBlock(true), createElementBlock(Fragment, null, renderList(connectionInterfaces.value, (connection) => {
                return openBlock(), createElementBlock("div", {
                  key: connection.connectionName,
                  class: "secret-item"
                }, [
                  createBaseVNode("div", _hoisted_9, [
                    createBaseVNode("div", _hoisted_10, [
                      _cache[7] || (_cache[7] = createBaseVNode("i", { class: "fa-solid fa-database" }, null, -1)),
                      createBaseVNode("span", null, toDisplayString(connection.connectionName), 1),
                      createBaseVNode("span", _hoisted_11, toDisplayString(connection.databaseType), 1)
                    ]),
                    createBaseVNode("div", _hoisted_12, [
                      createBaseVNode("span", null, toDisplayString(connection.database ? connection.database : "No database specified"), 1),
                      _cache[8] || (_cache[8] = createBaseVNode("span", { class: "separator" }, "•", -1)),
                      createBaseVNode("span", null, toDisplayString(connection.host ? connection.host : "Using connection URL"), 1)
                    ])
                  ]),
                  createBaseVNode("div", _hoisted_13, [
                    createBaseVNode("button", {
                      type: "button",
                      class: "btn btn-secondary",
                      onClick: ($event) => showEditModal(connection)
                    }, _cache[9] || (_cache[9] = [
                      createBaseVNode("i", { class: "fa-solid fa-edit" }, null, -1),
                      createBaseVNode("span", null, "Modify", -1)
                    ]), 8, _hoisted_14),
                    createBaseVNode("button", {
                      type: "button",
                      class: "btn btn-danger",
                      onClick: ($event) => showDeleteModal(connection.connectionName)
                    }, _cache[10] || (_cache[10] = [
                      createBaseVNode("i", { class: "fa-solid fa-trash-alt" }, null, -1),
                      createBaseVNode("span", null, "Delete", -1)
                    ]), 8, _hoisted_15)
                  ])
                ]);
              }), 128))
            ]))
          ])
        ]),
        createVNode(unref(ElDialog), {
          modelValue: dialogVisible.value,
          "onUpdate:modelValue": _cache[1] || (_cache[1] = ($event) => dialogVisible.value = $event),
          title: isEditing.value ? "Edit Database Connection" : "Add Database Connection",
          width: "500px",
          "before-close": handleCloseDialog
        }, {
          default: withCtx(() => [
            _cache[12] || (_cache[12] = createBaseVNode("div", { class: "modal-description mb-3" }, [
              createBaseVNode("p", null, " Configure your database connection details. You can connect using either host/port information or a connection URL. ")
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
            createBaseVNode("div", _hoisted_16, [
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
const DatabaseManager_vue_vue_type_style_index_0_scoped_87a64956_lang = "";
const DatabaseManager = /* @__PURE__ */ _export_sfc(_sfc_main, [["__scopeId", "data-v-87a64956"]]);
export {
  DatabaseManager as default
};

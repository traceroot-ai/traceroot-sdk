diff --git a/examples/data_app/app.py b/examples/data_app/app.py
index 1234567..89abcde 100644
--- a/examples/data_app/app.py
+++ b/examples/data_app/app.py
@@ def update_response_chart(df):
-    if errors_found:
-        logger.error("Cannot create response chart: data validation failed")
-        return go.Figure().update_layout(
-            title="Response Times by Model - Data Validation Failed")
+    if errors_found:
+        logger.warning("Cannot create response chart: data validation failed")
+        fig = go.Figure()
+        fig.add_annotation(
+            text="Data validation failed",
+            showarrow=False,
+            xref="paper",
+            yref="paper",
+            x=0.5,
+            y=0.5
+        )
+        return fig.update_layout(
+            title="Response Times by Model - Data Validation Failed"
+        )
@@ def update_response_chart(df):
-    if processed_df.empty:
-        logger.error(
-            "DataFrame is empty after preprocessing"
-        )
-        return go.Figure().update_layout(
-            title="Response Times by Model - No Data"
-        )
+    if processed_df.empty:
+        logger.warning("No data available for response chart")
+        fig = go.Figure()
+        fig.add_annotation(
+            text="No data available",
+            showarrow=False,
+            xref="paper",
+            yref="paper",
+            x=0.5,
+            y=0.5
+        )
+        return fig.update_layout(
+            title="Response Times by Model - No Data"
+        )
@@ def update_accuracy_chart(df):
-    if errors_found:
-        logger.error("Cannot create accuracy chart: data validation failed")
-        return go.Figure().update_layout(
-            title="Model Accuracy Over Time - Data Validation Failed")
+    if errors_found:
+        logger.warning("Cannot create accuracy chart: data validation failed")
+        fig = go.Figure()
+        fig.add_annotation(
+            text="Data validation failed",
+            showarrow=False,
+            xref="paper",
+            yref="paper",
+            x=0.5,
+            y=0.5
+        )
+        return fig.update_layout(
+            title="Model Accuracy Over Time - Data Validation Failed"
+        )
@@ def update_accuracy_chart(df):
-    if processed_df.empty:
-        logger.error(
-            "DataFrame is empty after preprocessing"
-        )
-        return go.Figure().update_layout(
-            title="Model Accuracy Over Time - No Data"
-        )
+    if processed_df.empty:
+        logger.warning("No data available for accuracy chart")
+        fig = go.Figure()
+        fig.add_annotation(
+            text="No data available",
+            showarrow=False,
+            xref="paper",
+            yref="paper",
+            x=0.5,
+            y=0.5
+        )
+        return fig.update_layout(
+            title="Model Accuracy Over Time - No Data"
+        )

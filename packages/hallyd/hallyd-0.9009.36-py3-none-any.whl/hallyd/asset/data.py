# SPDX-FileCopyrightText: © 2025 Josef Hahn
# SPDX-License-Identifier: AGPL-3.0-only
import hallyd.fs as _fs


data_dir = _fs.Path(__file__).parent("-static")

helpers_dir = data_dir("helpers")

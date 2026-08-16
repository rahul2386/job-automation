import * as vscode from 'vscode';
import {
  ExtensionConfiguration,
  extensionConfigurationService,
} from '../utils/extension_configuration_service';
import { createFakePartial } from '../test_utils/create_fake_partial';
import { setupDuoAgentPlatformNextContext } from './duo_agent_platform_new_ui_context';
import { FeatureFlag } from './constants';

jest.mock('../utils/extension_configuration_service', () => ({
  extensionConfigurationService: {
    getConfiguration: jest.fn(),
    onChange: jest.fn(),
  },
}));

const CONTEXT_KEY = 'gitlab:duoAgentPlatformNewUIConfigured';

describe('setupDuoAgentPlatformNextContext', () => {
  const mockFlagValue = (value: unknown) => {
    jest.mocked(extensionConfigurationService.getConfiguration).mockReturnValue(
      createFakePartial<ExtensionConfiguration>({
        featureFlags: { [FeatureFlag.DuoAgentPlatformNext]: value as boolean },
      }),
    );
  };

  const latestContextValue = () => {
    const calls = jest
      .mocked(vscode.commands.executeCommand)
      .mock.calls.filter(([command, key]) => command === 'setContext' && key === CONTEXT_KEY);

    return calls.length ? calls[calls.length - 1][2] : undefined;
  };

  const latestChangeListener = () => {
    const { calls } = jest.mocked(extensionConfigurationService.onChange).mock;

    return calls[calls.length - 1][0];
  };

  beforeEach(() => {
    jest.mocked(vscode.commands.executeCommand).mockClear();
    jest.mocked(extensionConfigurationService.onChange).mockClear();
  });

  it.each`
    value        | configured
    ${true}      | ${true}
    ${false}     | ${true}
    ${null}      | ${false}
    ${undefined} | ${false}
  `('publishes configured=$configured when the flag is $value', async ({ value, configured }) => {
    mockFlagValue(value);

    await setupDuoAgentPlatformNextContext();

    expect(latestContextValue()).toBe(configured);
  });

  it('updates the context when the flag configuration changes', async () => {
    mockFlagValue(null);
    await setupDuoAgentPlatformNextContext();
    expect(latestContextValue()).toBe(false);

    mockFlagValue(false);
    await latestChangeListener()(createFakePartial<ExtensionConfiguration>({}));

    expect(latestContextValue()).toBe(true);
  });
});
